import curses
import random
from structs import CellType
from world import World
from threading import Thread

class RenderThread(Thread):
    def __init__(self, window, world: World):
        Thread.__init__(self)

        self.win = window
        self.world = world
        self.running = True
    
    def run(self):
        self.exc = None
        try:
            while self.running:
                self.win.timeout(1000//20) # 20 FPS

                key = self.win.getch()

                # Quit
                if key == ord('q'):
                    break
                
                # Display world
                for x in range(self.world.width):
                    for y in range(self.world.height):
                        if not (x == self.world.width-1 and y == self.world.height-1):
                            cell = self.world[x,y]
                            self.win.addch(y, x, cell.ch(), curses.color_pair(cell.clr()))

                # Render robots
                for agent in self.world.agents:
                    info = self.world.agent_info(agent)
                    if info.holding is None:
                        ct = CellType.ROBOT
                        self.win.addch(info.y, info.x, ct.ch(), curses.color_pair(ct.clr()))
                    else:
                        ct = CellType.ROBOT_W_OBJECT
                        self.win.addch(info.y, info.x, ct.ch(), curses.color_pair(ct.clr()))

                self.win.refresh()


            curses.nocbreak()
            curses.echo()
            curses.endwin()
        except BaseException as e:
            self.exc = e

    def join(self):
        Thread.join(self)
        if self.exc:
            raise self.exc