import xml.etree.ElementTree as ET
from recognition.rules import astree
from pprint import pprint

class SrgsXmlConverter:

    def __init__(self, node_ids, named_rules):
        self.grammar_attrib = {
            'version': '1.0',
            'mode': 'voice',
            'xmlns': 'http://www.w3.org/2001/06/grammar',
            'xml:lang': 'en-US',
            'root': 'root',
            'tag-format': 'semantics/1.0'
        }
        self.node_ids = node_ids
        self.named_rules = named_rules
        self.map_rule_node_to_name = {v: k for k, v in named_rules.items()}
        self.root = ET.Element('grammar', attrib=self.grammar_attrib)
        self.ruleref_container_id = 'ruleref_container'

    def build_grammar(self, rules):
        self.root = ET.Element('grammar', attrib=self.grammar_attrib)
        self.root.append(self.build_root_rule())
        top_level_choices = self.build_top_level_choices()
        for rule_node in rules:
            rule_name = self.map_rule_node_to_name.get(rule_node)
            if rule_name is None or not rule_name.startswith('_'):
                self.append_rule_node(rule_node, top_level_choices)
        return self.root

    def append_rule_node(self, rule_node, top_level_choices):
        rule = self.convert_rule_element(rule_node)
        self.root.append(rule)
        if rule_node not in self.map_rule_node_to_name:
            top_level_choices.append(self.get_ruleref_item(self.node_ids[rule_node]))

    def build_root_rule(self):
        root_rule = ET.Element('rule', attrib={'id': self.grammar_attrib['root']})
        item = ET.Element('item')
        item.append(self.get_ruleref_item(self.ruleref_container_id))
        root_rule.append(item)
        return root_rule

    def build_top_level_choices(self):
        ruleref_container = ET.Element('rule', attrib={'id': self.ruleref_container_id})
        self.root.append(ruleref_container)
        repeat_item = ET.Element('item', attrib={'repeat': '1-'})
        top_level_choices = ET.Element('one-of', attrib={})
        repeat_item.append(top_level_choices)
        ruleref_container.append(repeat_item)
        return top_level_choices
    
    def get_ruleref_item(self, ruleid, low=1, high=1):
        ruleref_item = ET.Element('item')
        ruleref = ET.Element('ruleref', attrib={'uri': f'#{ruleid}'})
        self.apply_repeat_attrib(ruleref_item, low, high)
        ruleref_item.append(ruleref)
        return ruleref_item

    def convert_rule_element(self, rule_node):
        rule = ET.Element('rule', attrib={'id': self.node_ids[rule_node]})
        choices = ET.Element('one-of')
        rule.append(choices)
        self.fill_choices(rule_node.root, choices)
        return rule

    def fill_choices(self, node: astree.GroupingNode, choices):
        for seq in node.sequences:
            choices.append(ET.Element('item'))
            for child in seq:
                if isinstance(child, astree.WordNode):
                    self.add_text_to_item_elem(choices[-1], child, node)
                elif isinstance(child, astree.GroupingNode):
                    self.add_grouping(child, choices)
                elif isinstance(child, astree.RuleReference):
                    self.add_rule_reference(child, choices)
                else:
                    raise TypeError(f'Unable to serialize element {child}')

    def add_rule_reference(self, ruleref_node, choices):
        if ruleref_node.rule_name == '_dictation':
            # '<ruleref uri="grammar:dictation" type="application/srgs+xml"/><tag>out.SpokenText=rules.latest();</tag>'
            ruleref = ET.Element('ruleref', attrib={'uri': 'grammar:dictation', 'type': 'application/srgs+xml'})
            choices[-1].append(ruleref)
            return
        # all rule nodes here should be copies that refer to base rule
        base_rule = self.named_rules[ruleref_node.rule_name]
        rritem = self.get_ruleref_item(self.node_ids[base_rule],
                low=ruleref_node.repeat_low, high=ruleref_node.repeat_high)
        choices[-1].append(rritem)
        
    def add_grouping(self, child: astree.GroupingNode, choices):
        rule = ET.Element('rule', attrib={'id': self.node_ids[child]})
        self.root.append(rule)
        child_choices = ET.Element('one-of')
        rule.append(child_choices)
        rritem = self.get_ruleref_item(self.node_ids[child], low=child.repeat_low, high=child.repeat_high)
        choices[-1].append(rritem)
        self.fill_choices(child, child_choices)
    
    def add_text_to_item_elem(self, parent_elem, word_node, parent_node):
        assert self.get_repeat_vals(parent_elem) == (1, 1)
        if (not parent_elem or parent_elem[-1].tag != 'item' or
        (parent_elem[-1] and parent_elem[-1].find('ruleref') is not None) or
        not word_node.is_single):
            parent_elem.append(ET.Element('item'))
        self.apply_repeat_attrib(parent_elem[-1], word_node.repeat_low, word_node.repeat_high)
        self.append_text(parent_elem[-1], word_node.text)

    def apply_repeat_attrib(self, elem, low, high):
        elem.attrib.pop('repeat', None)
        if (low, high) != (1, 1):
            elem.attrib['repeat'] = f'{low or 0}-{high or 99}'

    def append_text(self, elem, text):
        elem.text = text if elem.text is None else f'{elem.text} {text}'

    def get_repeat_vals(self, elem):
        repeat_str = elem.attrib.get('repeat', '1-1')
        low, high = repeat_str.split('-')
        return int(low) if low else 0, int(high) if high else None

    