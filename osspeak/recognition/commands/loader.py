from profile import Profiler
import itertools
from recognition.actions import library
import uuid
import os
import os.path
import xml.etree.ElementTree as ET
import copy
import re
import collections
import json
import log
import recognition.actions.library.state
from recognition.actions import perform
import settings
from recognition.actions import variables, perform
from recognition.commands import grammar
from recognition import command_module
from recognition.rules.converter import SrgsXmlConverter
from recognition.rules import astree
from communication import pubsub, topics
from common import limited_size_dict

DEFAULT_DIRECTORY_SETTINGS = {
    'recurse': True,
    'conditions': {},
}

CONFIG_FILE_CACHE = limited_size_dict.LimitedSizeDict(size_limit=1000)

class CommandModuleController:

    def __init__(self, module_loader):
        self.module_loader = module_loader
        self.grammars = collections.OrderedDict()
        self.map_grammar_to_commands = collections.OrderedDict()
        self.command_modules = {}
        self.active_command_modules = {}

    def populate(self):
        self.command_modules = self.initialize_command_modules()

    def initialize_command_modules(self):
        command_module_json = self.module_loader.load_files()
        command_modules = {path: command_module.CommandModule(config, path) for path, config in command_module_json.items()}
        return command_modules
        
    def get_active_modules(self, current_window: str, current_state):
        active_modules = {}
        for path, cmd_module in self.command_modules.items():
            if cmd_module.is_active(current_window, current_state):
                active_modules[path] = cmd_module
        return active_modules

    async def load_modules(self, current_window, current_state, initialize: bool=False):
        previous_active_modules = self.active_command_modules
        if initialize:
            self.populate()
            self.load_command_module_information()
        self.active_command_modules = self.get_active_modules(current_window, current_state)
        namespace = self.get_namespace()
        self.fire_activation_events(previous_active_modules, namespace)
        grammar_context = self.build_grammar()
        self.save_grammar(grammar_context)
        grammar_xml, grammar_id = ET.tostring(grammar_context.xml).decode('utf8'), grammar_context.uuid
        await pubsub.publish_async(topics.LOAD_ENGINE_GRAMMAR, grammar_xml, grammar_id)

    def load_command_module_information(self):
        self.import_modules()
        self.load_functions()
        self.load_rules()
        self.load_commands()
        self.load_events()

    def import_modules(self):
        for cmd_module in self.command_modules.values():
            cmd_module.import_modules()

    def load_functions(self):
        for cmd_module in self.command_modules.values():
            cmd_module.define_functions()
        for cmd_module in self.command_modules.values():
            cmd_module.set_function_actions()

    def load_rules(self):
        for cmd_module in self.command_modules.values():
            cmd_module.load_rules()

    def load_commands(self):
        for cmd_module in self.command_modules.values():
            cmd_module.load_commands()

    def load_events(self):
        for cmd_module in self.command_modules.values():
            cmd_module.load_events()

    def load_initial_user_state(self):
        recognition.actions.library.state.USER_DEFINED_STATE = {}
        for path, cmd_module in self.command_modules.items():
            recognition.actions.library.state.USER_DEFINED_STATE.update(cmd_module.initial_state)

    def build_grammar(self) -> grammar.GrammarContext:
        named_rules, command_rules = self.get_active_rules()
        all_rules = list(named_rules.values()) + command_rules
        node_ids = self.generate_node_ids(all_rules, named_rules)
        active_commands = self.get_active_commands()
        namespace = self.get_namespace()
        command_contexts = {}
        for cmd in active_commands:
            variable_tree = variables.RecognitionResultsTree(cmd.rule, node_ids, named_rules)
            command_contexts[node_ids[cmd.rule]] = cmd, variable_tree
        grammar_xml = self.build_grammar_xml(all_rules, node_ids, named_rules)
        grammar_context = grammar.GrammarContext(grammar_xml, command_contexts, active_commands, namespace, named_rules, node_ids)
        return grammar_context

    def get_namespace(self):
        ns = library.namespace.copy()
        for mod in self.active_command_modules.values():
            ns.update(mod.functions)
        return ns

    def save_grammar(self, grammar):
        # remove oldest grammar if needed
        if len(self.grammars) > 4:
            self.grammars.popitem(last=False)
        self.grammars[grammar.uuid] = grammar

    def generate_node_ids(self, rules, named_rule_map):
        node_ids = {}
        for rule in rules:
            for node in rule.walk(rules=named_rule_map):
                if node not in node_ids:
                    node_ids[node] = f'n{len(node_ids) + 1}'
        return node_ids

    def fire_activation_events(self, previous_active_modules, namespace):
        previous_names, current_names = set(previous_active_modules), set(self.active_command_modules)
        for deactivated_name in previous_names - current_names:
            cmd_module = previous_active_modules[deactivated_name]
            if 'deactivate' in cmd_module.events:
                action = cmd_module.events['deactivate']
                perform.perform_action_from_event(action, namespace)
        for activated_name in current_names - previous_names:
            cmd_module = self.active_command_modules[activated_name]
            if 'activate' in cmd_module.events:
                action = cmd_module.events['activate']
                perform.perform_action_from_event(action, namespace)

    def build_grammar_xml(self, all_active_rules, node_ids, named_rules):
        return SrgsXmlConverter(node_ids, named_rules).build_grammar(all_active_rules)

    def get_active_rules(self):
        rules = {}
        rules.update(self.special_rules())
        command_rules = []
        for cmd_module in self.active_command_modules.values():
            rules.update(cmd_module.rules)
            command_rules.extend(cmd.rule for cmd in cmd_module.commands)
        return rules, command_rules

    def special_rules(self):
        return {'_dictate': astree.Rule()}

    def get_active_commands(self):
        grouped_commands = [m.commands for m in self.active_command_modules.values()]
        return list(itertools.chain.from_iterable(grouped_commands))
    
class StaticFileCommandModuleLoader:

    def __init__(self, root):
        self.root = root
        self.file_cache = limited_size_dict.LimitedSizeDict(size_limit=1000)

    def load_files(self):
        json_module_objects = {}
        command_dir = settings.settings['command_directory']
        if not os.path.isdir(command_dir):
            os.makedirs(command_dir)
        json_module_objects = self.load_json_directory(self.root, DEFAULT_DIRECTORY_SETTINGS)
        return json_module_objects

    def load_json_directory(self, path: str, parent_directory_settings):
        command_modules = {}
        directories = []
        local_settings = settings.try_load_json_file(os.path.join(path, '.osspeak.json'))
        directory_settings = {**parent_directory_settings, **local_settings}
        with os.scandir(path) as i:
            for entry in sorted(i, key=lambda x: x.name):
                if entry.name.startswith('.'):
                    continue
                if entry.is_file() and entry.name.endswith('.json'):
                    path = entry.path
                    file = self.file_cache.get(path, CommandModuleFile(path))
                    file.load_contents()
                    self.file_cache[path] = file
                    command_modules[path] = file.contents
                # read files in this directory first before recursing down
                elif entry.is_dir():
                    directories.append(entry)
            if directory_settings['recurse']:
                for direntry in directories:
                    command_modules.update(self.load_json_directory(direntry.path, directory_settings))
        return command_modules

class CommandModuleFile:

    def __init__(self, path):
        self.path = path
        self.last_modified = None
        self.contents = None

    def load_contents(self):
        last_modified = os.path.getmtime(self.path)
        if self.last_modified is None or last_modified > self.last_modified:
            self.last_modified = last_modified
            with open(self.path) as f:
                try:
                    self.contents = json.load(f)
                except json.decoder.JSONDecodeError as e:
                    self.contents = {'Error': str(e)}
                    log.logger.warning(f"JSON error loading command module '{path}':\n{e}")