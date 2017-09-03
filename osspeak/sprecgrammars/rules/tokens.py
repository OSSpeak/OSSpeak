import ast

from sprecgrammars.actions import parser, actionstream, pyexpr, asttransform
from sprecgrammars import api
from sprecgrammars.actions.action import Action

def action_substitute_validator(expr):
    return not (isinstance(expr.body, ast.BinOp) and isinstance(expr.body.op, ast.BitOr))

class BaseToken:
    pass

class WordToken(BaseToken):
    
    def __init__(self, text):
        self.text = text

class OrToken(BaseToken):
    pass

class GroupingOpeningToken(BaseToken):
    pass

class GroupingClosingToken(BaseToken):
    pass    

class OptionalGroupingOpeningToken(BaseToken):
    pass

class OptionalGroupingClosingToken(BaseToken):
    pass    

class NamedRuleToken(BaseToken):
    
    def __init__(self, name):
        self.name = name

class RepetitionToken(BaseToken):

    def __init__(self, low=0, high=None):
        self.low = low
        self.high = high

class ActionSubstituteToken(BaseToken):
    
    def __init__(self, text, defined_functions=None):
        self.text = text
        exprs = pyexpr.compile_python_expressions(text, action_substitute_validator, raise_on_error=False)
        self.action = Action(exprs, defined_functions)
        self.consumed_char_count = sum(len(e) for e in exprs)
        # action_parser = parser.ActionParser(text, defined_functiorns=defined_functions)
        # self.action = action_parser.parse(substitute=True)
        # self.consumed_char_count = sum(t.character_count for t in action_parser.parsed_tokens)