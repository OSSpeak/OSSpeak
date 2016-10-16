import json
from communication.procs import EngineProcessManager
from client import cmdmodule

class EventDispatcher:

    def __init__(self):
        self.cmd_module_watcher = cmdmodule.CommandModuleWatcher()
        self.start_engine_process()
        self.start_module_watcher()
        self.engine_process.start_engine_listening()

    def start_engine_process(self):
        self.engine_process = EngineProcessManager(self.cmd_module_watcher)
        self.engine_process.start_stdout_listening()

    def start_module_watcher(self):
        self.cmd_module_watcher.load_command_json()
        self.cmd_module_watcher.create_rule_grammar_nodes()
        self.cmd_module_watcher.create_grammar_nodes()
        self.cmd_module_watcher.serialize_scope_xml(None)

    def main_loop(self):
        menu.Menu(self).prompt_input()