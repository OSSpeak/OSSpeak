import uuid
from typing import List, Dict
import lark
from recognition.rules import astree

grammar_cache = {}

def build_repeat(node):
    if node.repeat_low == 1 and node.repeat_high == 1:
        return ''
    low = node.repeat_low
    if low == 0 and node.repeat_high is None:
        return '*'
    if low == 1 and node.repeat_high is None:
        return '+'
    if low == 0 and node.repeat_high == 1:
        return '?'
    high = 99 if node.repeat_high is None else node.repeat_high 
    return f'~{low}' if low == high else f'~{low}..{high}'

def parse_word(node: astree.WordNode, internal_rules, node_ids, named_rules):
    return build_lark_rule(node, f'"{node.text}"', internal_rules, node_ids)

def parse_rule_reference(node: astree.RuleReference, internal_rules, node_ids, named_rules):
    referenced_rule = named_rules[node.rule_name]
    referenced_rule_id = node_ids[referenced_rule]
    return build_lark_rule(node, referenced_rule_id, internal_rules, node_ids)

def build_lark_rule(node, parsed_text, internal_rules, node_ids):
    repeat = build_repeat(node)
    node_id = node_ids[node]
    internal_rules[node_id] = parsed_text + repeat
    return node_id

def parse_rule(node, internal_rules, node_ids, named_rules):
    lark_text = parse_grouping(node.root, internal_rules, node_ids, named_rules)
    return lark_text

def parse_grouping(node: astree.GroupingNode, internal_rules, node_ids, named_rules):
    sequences = []
    for seq in node.sequences:
        sequence_items = []
        for child in seq:
            seq_text = parse_functions[type(child)](child, internal_rules, node_ids, named_rules)
            sequence_items.append(seq_text)
        joined_items = ' '.join(sequence_items)
        need_parens = len(sequence_items) > 1
        sequences.append(f"({joined_items})" if need_parens else joined_items)
    joined_sequences = ' | '.join(sequences)
    lark_text = f'({joined_sequences})'
    return build_lark_rule(node, lark_text, internal_rules, node_ids)

parse_functions = {
    astree.GroupingNode: parse_grouping,
    astree.WordNode: parse_word,
    astree.RuleReference: parse_rule_reference
}

def create_lark_grammar(command_rules, named_rules, node_ids):
    lark_rules = create_lark_grammar_list(command_rules, named_rules, node_ids)

    rule_lines = [f'{rule_name}: {rule_text}' for rule_name, rule_text in lark_rules]
    rule_names = ' | '.join([node_ids[c] for c in command_rules])
    dictation_rule = named_rules['_dictate']
    dictation_rule_id = node_ids[dictation_rule]
    rule_lines.append(rf'{dictation_rule_id}: /(.+)+/')
    rule_lines.append('%import common.WORD')
    rule_lines.append('%ignore " "')
    rule_lines.append(f'start: ({rule_names})+')
    text = '\n'.join(rule_lines)
    if text in grammar_cache:
        gram = grammar_cache[text]
    else:
        gram = lark.Lark(text, start='start')
        grammar_cache[text] = gram
    return gram

def create_lark_grammar_list(command_rules: List, named_rules, node_ids):
    lark_named_rules = {}
    lark_command_rules = {}
    lark_internal_rules = {}
    for rule_name, rule in named_rules.items():
        if not rule_name.startswith('_'):
            lark_named_rules[node_ids[rule]] = parse_rule(rule, lark_internal_rules, node_ids, named_rules)
    for rule in command_rules:
        lark_command_rules[node_ids[rule]] = parse_rule(rule, lark_internal_rules, node_ids, named_rules)
    return [(k, v) for k, v in {**lark_named_rules, **lark_command_rules, **lark_internal_rules}.items()]

def yield_paths(lark_node, node_map, named_rules, ancestor_path=()):
    path = ancestor_path + (lark_node.data,)
    node = node_map[path]
    matched_text = node_text(node, lark_node, named_rules)
    yield path, matched_text
    for child in lark_node.children:
        if isinstance(child, lark.Tree):
            yield from yield_paths(child, node_map, named_rules, path)

def node_text(node, lark_node, named_rules):
    if isinstance(node, astree.WordNode):
        return node.text
    elif isinstance(node, astree.Rule) and named_rules['_dictate'] is node:
        return lark_node.children[0]