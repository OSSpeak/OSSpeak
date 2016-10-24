import collections
import itertools

from sprecgrammars.actions.parser import ActionParser
from sprecgrammars.actions import nodes
from client import commands
from sprecgrammars.formats.rules import astree
from sprecgrammars.formats import RuleParser, SrgsXmlConverter

class CommandModule:

    def __init__(self, config):
        self.config = config
        self.commands = []
        self.variables = []

    def load_commands(self, varmap):
        for rule_text, action_text in self.config['Commands']:
            cmd = Command(rule_text, action_text, variables=varmap)
            self.commands.append(cmd)

    def load_variables(self, varmap):
        for varname, rule_text in self.config['Variables']:
            var = astree.VariableNode(varname, rule_text, varmap)
            varmap[varname] = var
            self.variables.append(var)

class Command:
    
    def __init__(self, rule_text, action_text, variables=None):
        self.variables = variables
        self.init_rule(rule_text)
        self.init_action(action_text)

    def init_rule(self, rule_text):
        self.rule_text = rule_text
        parser = RuleParser(self.rule_text, self.variables)
        self.rule = parser.parse_as_rule()

    def init_action(self, action_text):
        self.action_text = action_text
        parser = ActionParser(self.action_text)
        self.action = parser.parse()

    def perform_action(self, engine_result):
        # empty variables dict, gets filled based on result
        bound_variables = self.rule.grouping_variables.copy()
        for k in bound_variables:
            bound_variables[k] = None
        i = 0
        while i < len(engine_result['Variables']):
            increment = self.bind_variable(bound_variables, engine_result['Variables'], i)
            i += increment
        print(engine_result['Variables'], bound_variables)
        var_list = list(bound_variables.values())
        self.action.perform(var_list)

    def bind_variable(self, bound_variables, semantic_variables, idx):
        var_id, var_text = semantic_variables[idx]
        increment = 1
        grouping_node = self.rule.grouping_variables.get(var_id)
        if grouping_node is None:
            return increment
        if bound_variables[var_id] is None:
            bound_variables[var_id] = nodes.RootAction()
        var_action = bound_variables[var_id]
        idx += 1
        while idx < len(semantic_variables):
            remaining_id, remaining_text = semantic_variables[idx]
            if remaining_id == 'literal-{}'.format(var_id):
                var_action.children.append(nodes.LiteralKeysAction(remaining_text))
                idx += 1
                increment += 1
            elif remaining_id in grouping_node.child_ids:
                remaining_increment = self.bind_variable(bound_variables, semantic_variables, idx)
                idx += remaining_increment
                increment += remaining_increment
            else:
                break
        return increment

    @property
    def id(self):
        return self.rule.id