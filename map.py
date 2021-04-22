import random
import curses
from world import World, CellType

#initialize screen
sc = curses.initscr()
curses.noecho()
h, w = 20, 40
win = curses.newwin(h, w, 0, 0)

robot_pos = [0,0]

win.keypad(1)
curses.curs_set(0)

world = World(width=w, height=h)

while True:
    win.timeout(1000//60) # 60 FPS

    key = win.getch()

    # Quit
    if key == ord('q'):
        break

    if key == curses.KEY_UP:
        robot_pos[1] -= 1
    if key == curses.KEY_DOWN:
        robot_pos[1] += 1
    if key == curses.KEY_LEFT:
        robot_pos[0] -= 1
    if key == curses.KEY_RIGHT:
        robot_pos[0] += 1

    if robot_pos[0] < 0:
        robot_pos[0] = 0
    if robot_pos[1] < 0:
        robot_pos[1] = 0

    if robot_pos[0] >= w:
        robot_pos[0] = w-1
    if robot_pos[1] >= h:
        robot_pos[1] = h-1

    if robot_pos == [w-1, h-1]:
        robot_pos = [w-1, h-2]
    
    world[random.randint(0,w-1), random.randint(0,h-1)] = CellType(random.randint(0,1))

    # Display world
    for x in range(w):
        for y in range(h):
            if not (x == w-1 and y == h-1):
                win.addch(y, x, world[x,y].ch())

    win.addch(robot_pos[1], robot_pos[0], 'R')

    win.refresh()


curses.nocbreak()
curses.echo()
curses.endwin()