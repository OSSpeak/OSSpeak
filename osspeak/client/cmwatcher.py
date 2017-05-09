import os
import json
import threading
import collections
import tempfile
import log
from sprecgrammars.actions.parser import ActionParser
import sprecgrammars.functions.library.state
from user import settings
from interfaces.gui import serializer
from client import commands, scopes, action, userstate
from sprecgrammars.rules import astree
from sprecgrammars.rules.parser import RuleParser
from sprecgrammars.rules.converter import SrgsXmlConverter
from platforms import api
import xml.etree.ElementTree as ET
from communication import messages
import time

class CommandModuleWatcher:

    def __init__(self):
        self.initial = True
        self.command_map = {}
        self.modules_to_save = {}
        self.command_module_json = self.load_command_json()
        self.shutdown = threading.Event()
        self.loading_lock = threading.Lock()
        messages.subscribe(messages.STOP_MAIN_PROCESS, lambda: self.shutdown.set())
        messages.subscribe(messages.PERFORM_COMMANDS, self.perform_commands)
        messages.subscribe(messages.SET_SAVED_MODULES, self.update_modules)

    def load_modules(self, current_window, current_state, reload_files=False):
        previous_active_modules = self.active_modules
        if reload_files:
            self.load_initial_user_state()
            self.command_module_json = self.load_command_json()
        self.initialize_modules()
        self.flag_active_modules(current_window, current_state)
        grammar_node = self.load_command_module_information()
        self.fire_activation_events(previous_active_modules)
        self.send_module_information_to_ui()
        grammar_xml = self.serialize_scope_xml(grammar_node)
        messages.dispatch(messages.LOAD_GRAMMAR,
                        self.initial,
                        ET.tostring(grammar_xml).decode('utf8'))
        self.initial = False

    def initialize_modules(self):
        self.init_fields()
        self.load_command_modules()
        self.load_scopes()

    def fire_activation_events(self, previous_active_modules):
        previous_names, current_names = set(previous_active_modules), set(self.active_modules)
        for deactivated_name in previous_names - current_names:
            cmd_module = previous_active_modules[deactivated_name]
            if 'deactivate' in cmd_module.events:
                cmd_module.events['deactivate'].perform(variables=[])
        for activated_name in current_names - previous_names:
            cmd_module = self.active_modules[activated_name]
            if 'activate' in cmd_module.events:
                cmd_module.events['activate'].perform(variables=[])

    def init_fields(self):
        self.grouped_titles = collections.defaultdict(set)
        # start with global scope
        self.scope_groupings = {'': scopes.Scope()}
        self.cmd_modules = {}
        self.active_modules = {}
        self.previous_command_map = self.command_map
        # key is string id, val is Action instance
        self.command_map = {}

    def load_command_json(self):
        json_module_dicts = {}
        command_dir = settings.user_settings['command_directory']
        if not os.path.isdir(command_dir):
            os.makedirs(command_dir)
        for root, dirs, filenames in os.walk(command_dir):
            # skip hidden directories such as .git
            dirs[:] = sorted([d for d in dirs if not d.startswith('.')])
            self.load_json_directory(filenames, command_dir, root, json_module_dicts)
        return json_module_dicts

    def load_json_directory(self, filenames, command_dir, root, json_module_dicts):
        for fname in filenames:
            if not fname.endswith('.json'):
                continue
            full_path = os.path.join(root, fname)
            partial_path = full_path[len(command_dir) + 1:]
            log.logger.debug(f"Loading command module '{partial_path}'...")
            with open(full_path) as f:
                try:
                    module_config = json.load(f)
                except json.decoder.JSONDecodeError as e:
                    module_config = {'Error': str(e)}
                    log.logger.warning(f"JSON error loading command module '{partial_path}':\n{e}")
                json_module_dicts[partial_path] = module_config

    def load_command_modules(self):
        for path, config in self.command_module_json.items():
            cmd_module = commands.CommandModule(config, path)
            self.cmd_modules[path] = cmd_module

    def load_scopes(self):
        for path, cmd_module in self.cmd_modules.items():
            scope_name = cmd_module.config.get('scope', '')
            if scope_name not in self.scope_groupings:
                global_scope = self.scope_groupings['']
                self.scope_groupings[scope_name] = scopes.Scope(global_scope, name=scope_name)
            self.scope_groupings[scope_name].cmd_modules[path] = cmd_module
            cmd_module.scope = self.scope_groupings[scope_name]

    def load_initial_user_state(self):
        sprecgrammars.functions.library.state.USER_DEFINED_STATE = {}
        for path, cmd_module in self.cmd_modules.items():
            initial_state = {k: eval(v) for k, v in cmd_module.initial_state.items()}
            sprecgrammars.functions.library.state.USER_DEFINED_STATE.update(initial_state)
 
    def flag_active_modules(self, current_window, current_state):
        for path, cmd_module in self.get_active_modules(current_window, current_state):
            self.active_modules[path] = cmd_module

    def get_active_modules(self, current_window, current_state):
        for path, cmd_module in self.cmd_modules.items():
            is_active = self.is_command_module_active(cmd_module, current_window, current_state)
            if is_active:
                yield path, cmd_module

    def is_command_module_active(self, cmd_module, current_window, current_state):
        title_filter = cmd_module.conditions.get('title')
        current_window_matches = title_filter is None or title_filter.lower() in current_window.lower() 
        return current_window_matches and cmd_module.state_active(current_state)

    def load_command_module_information(self):
        grammar_node = astree.GrammarNode()
        self.load_functions()
        self.load_rules(grammar_node)
        self.load_commands(grammar_node)
        self.load_events()
        return grammar_node

    def load_functions(self):
        self.load_builtin_functions()
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.define_functions()
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.set_function_actions()

    def load_rules(self, grammar_node):
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.initialize_rules()
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.load_rules()
            for rule in cmd_module.rules:
                if path in self.active_modules:
                    grammar_node.rules.append(rule)

    def load_commands(self, grammar_node):
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.load_commands()
            for cmd in cmd_module.commands:
                self.command_map[cmd.id] = cmd
                if path in self.active_modules:
                    grammar_node.rules.append(cmd.rule)
    
    def load_builtin_functions(self):
        from sprecgrammars.api import rule
        global_scope = self.scope_groupings['']
        global_scope.rules['_dictate'] = rule('', '_dictate')

    def load_events(self):
        for path, cmd_module in self.cmd_modules.items():
            cmd_module.load_events()

    def serialize_scope_xml(self, grammar_node):
        converter = SrgsXmlConverter()
        return converter.convert_grammar(grammar_node)

    def update_modules(self, modified_modules):
        raise NotImplementedError
        command_dir = settings.user_settings['command_directory']
        for path, cmd_module_config in modified_modules.items():
            self.command_module_json[path] = cmd_module_config
            with open(os.path.join(command_dir, path), 'w') as outfile:
                json.dump(cmd_module_config, outfile, indent=4)
        self.load_modules()

    def send_module_information_to_ui(self):
        payload = {'modules': self.cmd_modules}
        messages.dispatch(messages.LOAD_MODULE_MAP, payload)

    def perform_commands(self, command_results):
        action.perform_commands(command_results, self.command_map, self.previous_command_map)