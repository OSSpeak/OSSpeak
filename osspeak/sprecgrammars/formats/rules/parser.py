from sprecgrammars import tokens
from sprecgrammars.formats.baseparser import BaseParser
from sprecgrammars.formats.rules import ruletokstream, astree


class RuleParser(BaseParser):
    '''
    Convert a rule string i.e. 'hello (world|universe) into
    an abstract syntax tree of nodes that can be serialized
    into speech recognition grammar formats like SRGS XML. 
    '''

    def __init__(self, text, variables):
        super().__init__(text)
        self.variables = variables
        self.stream = ruletokstream.RuleTokenStream(self.text)
        self.grouping_stack = []
        self.groupings = []
        self.token_list = []
        self.parse_map = {
            tokens.WordToken: self.parse_word_token,
            tokens.OrToken: self.parse_or_token,
            tokens.ParenToken: self.parse_paren_token,
            tokens.RepetitionToken: self.parse_repetition_token,
            tokens.VariableToken: self.parse_variable_token,
        }

    def parse_as_rule(self):
        top_level_rule = astree.Rule()
        self.grouping_stack = [top_level_rule]
        for tok in self.stream:
            self.token_list.append(tok)
            self.parse_map[type(tok)](tok)
        for grouping in self.groupings + self.grouping_stack[1:]:
            top_level_rule.grouping_variables[grouping.id] = grouping
            top_level_rule.grouping_variables_values[grouping.id] = ''
        return top_level_rule

    def parse_word_token(self, tok):
        self.maybe_pop_top_grouping()
        word_node = astree.WordNode(tok.text)
        self.top.children.append(word_node)

    def parse_or_token(self, tok):
        self.maybe_pop_top_grouping()
        or_node = astree.OrNode()
        self.top.children.append(or_node)

    def parse_variable_token(self, tok):
        self.maybe_pop_top_grouping()
        var_node = self.variables[tok.name]
        self.top.children.append(var_node)

    def parse_paren_token(self, tok):
        self.maybe_pop_top_grouping()
        if tok.is_open:
            grouping_node = astree.GroupingNode()
            self.top.children.append(grouping_node)
            self.grouping_stack.append(grouping_node)
        else:
            self.top.open = False

    def parse_repetition_token(self, tok):
        if not self.top.open:
            repeated_node = self.top
        elif self.top.children:
            repeated_node = top.children[-1]
        else:
            self.croak('Invalid repetition')

    def apply_repetition(self, node, low=0, high=None):
        if low is not None:
            node.low = low

    def maybe_pop_top_grouping(self):
        if not self.top.open:
            grouping = self.grouping_stack.pop()
            self.groupings.append(grouping)

    @property
    def top(self):
        return self.grouping_stack[-1]
