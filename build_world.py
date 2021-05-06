from structs import CellType
from world import World

world = World(60, 20)

# Walls
for x in range(world.width):
    for y in range(world.height):
        if x == 0 or x == world.width-1 or y == 0 or y == world.height - 1:
            world[x, y] = CellType.OBSTACLE

for i in range(world.width):
    world[i, world.height // 2] = CellType.OBSTACLE

world[world.width // 2, world.height // 2] = CellType.FREE

# world[2, world.height // 3] = CellType.OBJECT

world[2, world.height // 3 * 2 - 1] = CellType.RETURN

world.to_file("basic.wrld")
