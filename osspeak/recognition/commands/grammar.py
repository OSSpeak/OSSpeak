import uuid
from typing import List, Dict
from recognition.rules import _lark
from common import limited_size_dict


class GrammarContext:
    
    def __init__(self, xml, command_modules, command_contexts, active_commands, namespace, named_rules, node_ids, utterance_priority):
        self.xml = xml
        self.uuid = str(uuid.uuid4())
        self.command_modules = command_modules
        self.command_contexts = command_contexts
        self.active_commands = active_commands 
        self.namespace = namespace
        self.node_ids = node_ids
        self.named_rules = named_rules
        command_rules = [cmd.utterance for cmd in active_commands]
        self.lark_grammar = _lark.create_lark_grammar(command_rules, named_rules, node_ids, utterance_priority)
        self.recognition_cache = limited_size_dict.LimitedSizeDict(size_limit=5000)

    def parse_recognition(self, text):
        if text in self.recognition_cache:
            return self.recognition_cache[text]
        match = self.lark_grammar.parse(text + ' ') # add a space at the end to account for lark grammar expecting a whitespace after every word
        self.recognition_cache[text] = match
        return match