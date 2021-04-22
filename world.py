from enum import Enum

celltype_to_char = {
    0: ' ',
    1: '#',
    2: 'R'
}

class CellType(Enum):
    FREE = 0
    ROBOT = 1
    OBSTACLE = 2

    def ch(self):
        return celltype_to_char[self.value]

    def __str__(self):
        return celltype_to_char[self.value] 

class World:
    def __init__(self, width=20, height=20) -> None:
        self.width = width
        self.height = height
        self.map = [[CellType.FREE for _ in range(height)] for _ in range(width)]

    def __getitem__(self, pos):
        x,y = pos
        return self.map[x][y]

    def __setitem__(self, pos, val):
        x,y = pos
        self.map[x][y] = val