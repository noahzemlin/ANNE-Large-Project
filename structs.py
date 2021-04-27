from enum import Enum

# 0 = white on black, 1 = green on black, 2 = cyan on black
class CellType(Enum):
    FREE = (' ', 0)
    ROBOT = ('R', 0)
    ROBOT_W_OBJECT = ('R', 1)
    OBJECT = ('O', 2)
    OBSTACLE = ('#', 0)

    def __init__(self, char, color):
        self.char = char
        self.color = color

    def ch(self):
        return self.char

    def clr(self):
        return self.color

    def __str__(self):
        return self.char

class AgentInfo():
    def __init__(self, x=0, y=0, holding=None):
        self.x = x
        self.y = y
        self.holding = holding