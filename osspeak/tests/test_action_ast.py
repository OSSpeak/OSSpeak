import pytest
import sys
import json
sys.path.insert(0, '../osspeak')
from recognition.actions import astree_constructor
import recognition.actions.context
import recognition.actions.library.clipboard
from recognition import lark_parser
from recognition.lark_parser import action_grammar

def test_call_args():
    text = "mouse.move(7, 8, y=$1, relative = true() )"
    action = text_to_action(text)
    assert_equal(action, {
        "args": [
            {
                "type": "Integer",
                "value": 7
            },
            {
                "type": "Integer",
                "value": 8
            }
        ],
        "fn": {
            "attribute_of": {
                "type": "Name",
                "value": "mouse"
            },
            "name": "move",
            "type": "Attribute"
        },
        "kwargs": {
            "relative": {
                "args": [],
                "fn": {
                    "type": "Name",
                    "value": "true"
                },
                "kwargs": {},
                "type": "Call"
            },
            "y": {
                "type": "Variable",
                "value": 1
            }
        },
        "type": "Call"
    })

# def test_call_args():
#     text = "mouse.move(7, 8, y=$1, relative = True )"
#     lark_ir = lark_parser.parse_action(text)
#     print(lark_ir.pretty())

# def test_call_chain():
#     text = "first.foo.bar.baz()"
#     lark_ir = lark_parser.parse_action(text)

def test_literal1():
    text = "hello there \tworld"
    action = text_to_action(text)
    assert_equal(action, {
        "type": "Literal",
        "value": "hello there \tworld"
    })

{
    "expressions": [
        {
            "type": "Literal",
            "value": "hello"
        },
        {
            "type": "ExprSequenceSeparator",
            "value": " "
        },
        {
            "expressions": [
                {
                    "type": "Literal",
                    "value": "there"
                },
                {
                    "type": "ExprSequenceSeparator",
                    "value": " \t"
                },
                {
                    "type": "Literal",
                    "value": "world"
                }
            ],
            "type": "ExpressionSequence"
        }
    ],
    "type": "ExpressionSequence"
}

def test_literal2():
    text = "Hello ',' $1"
    action = text_to_action(text)
    assert_equal(action, {
        "expressions": [
            {
                "type": "Literal",
                "value": "Hello"
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "type": "String",
                "value": ","
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "type": "Variable",
                "value": 1
            }
        ],
        "type": "ExpressionSequence"
    })

def test_call1():
    text = "repeat({$1}, $2)"
    action = text_to_action(text)
    assert_equal(action, {
        "args": [
            {
                "keys": {
                    "type": "Variable",
                    "value": 1
                },
                "type": "KeySequence"
            },
            {
                "type": "Variable",
                "value": 2
            }
        ],
        "fn": {
            "type": "Name",
            "value": "repeat"
        },
        "kwargs": {},
        "type": "Call"
    })

def test_variable1():
    text = "4 + $1"
    action = text_to_action(text)
    assert_equal(action,  {
        "left": {
            "type": "Integer",
            "value": 4
        },
        "right": {
            "type": "Variable",
            "value": 1
        },
        "type": "Add"
    })

def test_attribute1():
    text = "$1.upper()"
    action = text_to_action(text)
    assert_equal(action, {
        "args": [],
        "fn": {
            "attribute_of": {
                "type": "Variable",
                "value": 1
            },
            "name": "upper",
            "type": "Attribute"
        },
        "kwargs": {},
        "type": "Call"
    })

def test_ambig1():
    text = "'cd ..' + '/..' * int($1 || 0) {enter}"
    action = text_to_action(text)
    assert_equal(action, {
        "expressions": [
            {
                "left": {
                    "type": "String",
                    "value": "cd .."
                },
                "right": {
                    "left": {
                        "type": "String",
                        "value": "/.."
                    },
                    "right": {
                        "args": [
                            {
                                "left": {
                                    "type": "Variable",
                                    "value": 1
                                },
                                "right": {
                                    "type": "Integer",
                                    "value": 0
                                },
                                "type": "Or"
                            }
                        ],
                        "fn": {
                            "type": "Name",
                            "value": "int"
                        },
                        "kwargs": {},
                        "type": "Call"
                    },
                    "type": "Multiply"
                },
                "type": "Add"
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "keys": {
                    "type": "Literal",
                    "value": "enter"
                },
                "type": "KeySequence"
            }
        ],
        "type": "ExpressionSequence"
    })

def test_not():
    text = "!true()"
    action = text_to_action(text)
    assert_equal(action,  {
        "operand": {
            "args": [],
            "fn": {
                "type": "Name",
                "value": "true"
            },
            "kwargs": {},
            "type": "Call"
        },
        "operation": "not",
        "type": "UnaryOp"
    })
    assert evaluate_action(action) is False

def test_string1():
    text = "'http://news.ycombinator.com'"
    action = text_to_action(text)
    assert_equal(action,  {
        "type": "String",
        "value": "http://news.ycombinator.com"
    })

def test_add():
    text = "4 + 5"
    action = text_to_action(text)
    assert_equal(action,  {
        "left": {
            "type": "Integer",
            "value": 4
        },
        "right": {
            "type": "Integer",
            "value": 5
        },
        "type": "Add"
    })
    assert evaluate_action(action) == 9

def test_float1():
    text = "-4.5 .23 0.2"
    action = text_to_action(text)
    assert_equal(action,  {
        "expressions": [
            {
                "operand": {
                    "type": "Float",
                    "value": 4.5
                },
                "operation": "negative",
                "type": "UnaryOp"
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "type": "Float",
                "value": 0.23
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "type": "Float",
                "value": 0.2
            }
        ],
        "type": "ExpressionSequence"
    })

def test_argument_reference():
    text = "$foo $bar"
    action = text_to_action(text)
    assert_equal(action, {
        "expressions": [
            {
                "type": "ArgumentReference",
                "value": "foo"
            },
            {
                "type": "ExprSequenceSeparator",
                "value": " "
            },
            {
                "type": "ArgumentReference",
                "value": "bar"
            }
        ],
        "type": "ExpressionSequence"
    })

def test_multiple_args():
    text = "loop(hello, 10)"
    action = text_to_action(text)
    assert_equal(action,  {
        "args": [
            {
                "type": "Literal",
                "value": "hello"
            },
            {
                "type": "Integer",
                "value": 10
            }
        ],
        "fn": {
            "type": "Name",
            "value": "loop"
        },
        "kwargs": {},
        "type": "Call"
    })

def test_index():
    text = "[1,2,3][1]"
    action = text_to_action(text)
    assert_equal(action,  {
        "index": {
            "type": "Integer",
            "value": 1
        },
        "index_of": {
            "items": [
                {
                    "type": "Integer",
                    "value": 1
                },
                {
                    "type": "Integer",
                    "value": 2
                },
                {
                    "type": "Integer",
                    "value": 3
                }
            ],
            "type": "List"
        },
        "type": "Index"
    })
    context = recognition.actions.context.empty_recognition_context()
    assert action.evaluate(context) == 2

def test_slice():
    text = "[1, 2, 3][1:3]"
    action = text_to_action(text)
    assert_equal(action,  {
        "slice_of": {
            "items": [
                {
                    "type": "Integer",
                    "value": 1
                },
                {
                    "type": "Integer",
                    "value": 2
                },
                {
                    "type": "Integer",
                    "value": 3
                }
            ],
            "type": "List"
        },
        "start": {
            "type": "Integer",
            "value": 1
        },
        "step": None,
        "stop": {
            "type": "Integer",
            "value": 3
        },
        "type": "Slice"
    })
    context = recognition.actions.context.empty_recognition_context()
    assert action.evaluate(context) == [2, 3]

def test_order_of_operations1():
    text = "1+2*3"
    assert evaluate_action_text(text) == 7

def test_order_of_operations2():
    text = "1+(3*4)-9"
    assert evaluate_action_text(text) == 4

def test_order_of_operations3():
    text = "1+3*4-9"
    action = text_to_action(text)
    assert_equal(action, {
        "left": {
            "left": {
                "type": "Integer",
                "value": 1
            },
            "right": {
                "left": {
                    "type": "Integer",
                    "value": 3
                },
                "right": {
                    "type": "Integer",
                    "value": 4
                },
                "type": "Multiply"
            },
            "type": "Add"
        },
        "right": {
            "type": "Integer",
            "value": 9
        },
        "type": "Subtract"
    })
    assert evaluate_action(action) == 4

def test_order_of_operations4():
    text = "1 + 5 == 7 - 1"
    action = text_to_action(text)
    assert_equal(action, {
        "comparators": [
            {
                "left": {
                    "type": "Integer",
                    "value": 7
                },
                "right": {
                    "type": "Integer",
                    "value": 1
                },
                "type": "Subtract"
            }
        ],
        "left": {
            "left": {
                "type": "Integer",
                "value": 1
            },
            "right": {
                "type": "Integer",
                "value": 5
            },
            "type": "Add"
        },
        "ops": [
            "=="
        ],
        "type": "Compare"
    })
    assert evaluate_action(action) is True

def test_compare_chain():
    text = "1 < 3 <= 2 + 1"
    action = text_to_action(text)
    assert_equal(action,{
        "comparators": [
            {
                "type": "Integer",
                "value": 3
            },
            {
                "left": {
                    "type": "Integer",
                    "value": 2
                },
                "right": {
                    "type": "Integer",
                    "value": 1
                },
                "type": "Add"
            }
        ],
        "left": {
            "type": "Integer",
            "value": 1
        },
        "ops": [
            "<",
            "<="
        ],
        "type": "Compare"
    })
    assert evaluate_action(action) is True

def test_order_of_operations5():
    text = "2**3**1+2"
    action = text_to_action(text)
    assert_equal(action, {
        "left": {
            "left": {
                "type": "Integer",
                "value": 2
            },
            "right": {
                "left": {
                    "type": "Integer",
                    "value": 3
                },
                "right": {
                    "type": "Integer",
                    "value": 1
                },
                "type": "Exponent"
            },
            "type": "Exponent"
        },
        "right": {
            "type": "Integer",
            "value": 2
        },
        "type": "Add"
    })
    assert evaluate_action(action) == 10
    
def test_divide():
    text = "6 / 5"
    action = text_to_action(text)
    assert_equal(action, {
        "left": {
            "type": "Integer",
            "value": 6
        },
        "right": {
            "type": "Integer",
            "value": 5
        },
        "type": "Divide"
    })
    assert evaluate_action(action) == 1.2

def test_spacing():
    text = "$ 1"
    with pytest.raises(Exception):
        action = text_to_action("$ 1")
    with pytest.raises(Exception):
        action = text_to_action("foo . bar")
    with pytest.raises(Exception):
        text_to_action("foo. bar")
    with pytest.raises(Exception):
        action = text_to_action("foo .bar")
    with pytest.raises(Exception):
        text_to_action("foo . bar")
    text_to_action("foo.bar")

def evaluate_action(action):
    context = recognition.actions.context.empty_recognition_context()
    return action.evaluate(context)

def evaluate_action_text(text: str):
    action = text_to_action(text)
    context = recognition.actions.context.empty_recognition_context()
    return action.evaluate(context)

def to_clipboard(action):
    recognition.actions.library.clipboard.set(astree_constructor.to_json_string(action))

def assert_equal(action_node, json_value):
    assert json.loads(astree_constructor.to_json_string(action_node)) == json_value


def text_to_action(text):
    lark_ir = lark_parser.parse_action(text)
    return astree_constructor.action_from_lark_ir(lark_ir, text)

