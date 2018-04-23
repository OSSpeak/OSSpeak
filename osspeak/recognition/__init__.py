def rule(text, name=None):
    from recognition.rules.parser import RuleParser
    parser = RuleParser(text)
    rule_obj = parser.parse_as_rule(name=name)
    return rule_obj

def action(action_input, *args, **kwargs):
    from recognition.actions.action import Action
    from recognition.actions import piece
    if not isinstance (action_input, list):
        action_input = [action_input]
    action_objects = [{'type': 'dsl', 'value': x} if isinstance(x, str) else x for x in action_input]
    action_pieces = [piece.ActionPiece.from_object(obj) for obj in action_objects]
    return Action(action_pieces)

def function(func_signature, func_action=None):
    from recognition.actions.function import Function
    func = Function(func_signature, func_action)
    return func