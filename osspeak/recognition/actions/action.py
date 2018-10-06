from recognition.actions import library, pyexpr, asttransform, context, perform

class Action:
    
    def __init__(self, pieces):
        self.pieces = pieces

    def perform(self):
        for piece in self.pieces:
            piece.perform()