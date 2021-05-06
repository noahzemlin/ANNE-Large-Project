import copy
from simulator import SimulationThread

import numpy as np
from RaisingThread import RaisingThread
import curses
import random
from structs import CellType
from world import World
from threading import Thread

class RenderThread(RaisingThread):
    def __init__(self, window, sim_thread: SimulationThread):
        RaisingThread.__init__(self)

        self.sim = sim_thread
        self.win = window
        self.world = World()
        self.world.from_file("basic.wrld")
        self.running = True
    
    def run_w_exceptions(self):
        while self.running:
            # Display best agent
            agent = copy.deepcopy(self.sim.best_agent)

            self.world.reset()

            agent_clone = copy.deepcopy(agent)

            self.world.put_agent(agent, 4, 12)
            self.world.put_agent(agent_clone, 2, 12)

            agents = [agent, agent_clone]

            # Add 12 objects
            for _ in range(12):
                while not self.world.put_object((random.randint(3, 50), random.randint(3, 8))):
                    # Keep trying to place another object until it places
                    continue

            gen = self.sim.gen
            score = self.sim.best_fitness
            for _ in range(200):
                self.world.move_num += 1
                if not self.running:
                    break
                for agent in agents:
                    self.win.timeout(1000//40) # 40 FPS

                    if agent == None:
                        continue

                    key = self.win.getch()

                    input_vector = self.world.agent_to_vector(agent)

                    action_vector = agent.predict(input_vector)
                    action_index = np.argmax(action_vector)

                    self.world.perform_action(agent, action_index)

                    # Quit
                    if key == ord('q'):
                        self.running = False
                        break
                    
                    # Display world
                    for x in range(self.world.width):
                        for y in range(self.world.height):
                            if not (x == self.world.width-1 and y == self.world.height-1):
                                cell = self.world[x,y]
                                self.win.addch(y, x, cell.ch(), curses.color_pair(cell.clr()))

                    # Render robots
                    for agent in agents:
                        info = self.world.agent_info(agent)
                        if info.holding is None or info.holding == False:
                            ct = CellType.ROBOT
                            self.win.addch(info.y, info.x, ct.ch(), curses.color_pair(ct.clr()))
                        else:
                            ct = CellType.ROBOT_W_OBJECT
                            self.win.addch(info.y, info.x, ct.ch(), curses.color_pair(ct.clr()))

                    self.win.addstr(self.world.height, 0, f"Best from Gen {gen}, Fitness: {score:03.2f}")

                    self.win.refresh()


        curses.nocbreak()
        curses.echo()
        curses.endwin()