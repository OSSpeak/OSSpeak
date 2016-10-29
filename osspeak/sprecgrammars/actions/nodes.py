from platforms import api

class Action:

    def __init__(self):
        pass

    def evaluate(self):
        raise NotImplementedError

    def add(self, *a, **k):
        raise NotImplementedError

class RootAction(Action):

    def __init__(self):
        super().__init__()
        self.children = []

    def add(self, child):
        self.children.append(child)

    def perform(self, variables):
        for subaction in self.children:
            subaction.perform(variables)

class LiteralKeysAction(Action):
    
    def __init__(self, text):
        super().__init__()
        self.text = text

    def perform(self, variables):
        api.type_literal(self.text)

    def evaluate(self):
        return self.text

class FunctionCall(Action):

    def __init__(self, func_name):
        super().__init__()
        self.arguments = []
        self.func_name = func_name

    def add(self, node):
        self.arguments.append(node)

class KeySequence(Action):

    def __init__(self):
        super().__init__()
        self.keys = []

    def add(self, node):
        self.keys.append(node)

    def perform(self, variables):
        keypresses = [node.evaluate() for node in self.keys]
        api.type_keypresses(keypresses)

class PositionalVariable(Action):

    def __init__(self, pos):
        super().__init__()
        self.pos = pos

    def perform(self, variables):
        variables[self.pos - 1].perform(variables)

class WhitespaceNode(Action):

    def __init__(self, text):
        self.text = text

class AppendModifierNode(Action):

    def __init__(self):
        pass