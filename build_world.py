from structs import CellType
from world import World

world = World(40, 20)

# Walls
for x in range(world.width):
    for y in range(world.height):
        if x == 0 or x == world.width-1 or y == 0 or y == world.height - 1:
            world[x, y] = CellType.OBSTACLE

for i in range(world.width // 2):
    world[i, world.height // 2] = CellType.OBSTACLE

world[2, world.height // 3] = CellType.OBJECT

world.to_file("basic.wrld")
