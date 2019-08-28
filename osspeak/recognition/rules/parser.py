from recognition.rules import lexer, astree, tokens
from profile import Profiler

class RuleParser:
    '''
    Convert a rule string i.e. 'hello (world|universe)' into
    an abstract syntax tree of nodes that can be serialized
    into speech recognition grammar formats like SRGS XML. 
    '''

    def __init__(self, text, debug=False):
        self.text = text
        self.debug = debug
        self.lexer = lexer.RuleLexer(self.text)
        self.grouping_stack = []
        self.optional_groupings = set()
        self.repeated_nodes = set()
        self.closed_nodes = set()
        self.token_list = []
        self.parse_map = {
            tokens.WordToken: self.parse_word_token,
            tokens.OrToken: self.parse_or_token,
            tokens.GroupingOpeningToken: self.parse_grouping_opening_token,
            tokens.GroupingClosingToken: self.parse_grouping_closing_token,
            tokens.OptionalGroupingOpeningToken: self.parse_optional_grouping_opening_token,
            tokens.OptionalGroupingClosingToken: self.parse_optional_grouping_closing_token,
            tokens.RepetitionToken: self.parse_repetition_token,
            tokens.NamedRuleToken: self.parse_named_rule_token,
            tokens.ActionSubstituteToken: self.parse_action_substitute_token,
            tokens.WhitespaceToken: self.parse_whitespace_token,
        }

    def parse_as_rule(self):
        top_level_rule = astree.Rule(text=self.text)
        self.grouping_stack = [top_level_rule.root]
        for tok in self.lexer:
            self.token_list.append(tok)
            self.parse_map[type(tok)](tok)
        # valid_last_grouping = len(self.grouping_stack) == 1 or len(self.grouping_stack) == 2 and not self.grouping_stack[-1].open
        # assert self.grouping_stack[0] is top_level_rule and valid_last_grouping
        return top_level_rule

    def parse_word_token(self, tok):
        self.add_to_next_grouping(astree.WordNode(tok.text))

    def parse_or_token(self, tok):
        self.top.sequences.append([])

    def parse_named_rule_token(self, tok):
        self.add_to_next_grouping(astree.RuleReference(tok.name))

    def parse_grouping_opening_token(self, tok):
        grouping_node = astree.GroupingNode()
        self.add_to_next_grouping(grouping_node)
        self.grouping_stack.append(grouping_node)

    def parse_grouping_closing_token(self, tok):
        self.pop_top_grouping_if_closed()
        if self.top in self.optional_groupings:
            self.croak("Can't match '[' with ')'")
        self.closed_nodes.add(self.top)

    def parse_optional_grouping_opening_token(self, tok):
        self.parse_grouping_opening_token(tok)
        self.optional_groupings.add(self.top)
        self.apply_repetition(self.top, 0, 1)

    def parse_optional_grouping_closing_token(self, tok):
        if self.top not in self.optional_groupings:
            self.croak("Can't match '(' with ']'")
        self.pop_top_grouping_if_closed()
        self.closed_nodes.add(self.top)

    def parse_repetition_token(self, tok):
        repeated_node = self.modifiable_node
        self.apply_repetition(repeated_node, tok.low, tok.high)

    def parse_action_substitute_token(self, tok):
        self.modifiable_node.action_piece_substitute = tok.action_piece

    def parse_whitespace_token(self, tok):
        pass

    def pop_top_grouping_if_closed(self):
        if self.top in self.closed_nodes:
            grouping = self.grouping_stack.pop()

    @property
    def top(self):
        return self.grouping_stack[-1]

    @property
    def modifiable_node(self):
        if self.top in self.closed_nodes:
            return self.top
        if self.top.sequences and self.top.sequences[-1]:
            return self.top.sequences[-1][-1]
        self.croak('No modifiable rule node exists')

    def apply_repetition(self, node, low, high):
        if node in self.repeated_nodes:
            self.croak('Cannot apply repetition to node twice')
        self.repeated_nodes.add(node)
        node.repeat_low = low
        node.repeat_high = high

    def add_to_next_grouping(self, node):
        self.pop_top_grouping_if_closed()
        top_sequences = self.top.sequences
        if not top_sequences:
            top_sequences.append([])
        top_sequences[-1].append(node)


    def croak(self, message):
        raise RuntimeError(message)