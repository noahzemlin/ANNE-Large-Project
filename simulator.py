import logging
import numpy as np
from RaisingThread import RaisingThread
import random
from world import World
from threading import Thread
import time

class SimulationThread(RaisingThread):
    def __init__(self, world: World):
        RaisingThread.__init__(self)

        self.world = world
        self.running = True

    def run_w_exceptions(self):
        # Initalize population
        self.population = []

        while self.running:
            # Run one simulation
            for agent in self.world.agents:
                info = self.world.agent_info(agent)
                input_vector = self.world.info_to_vector(info)

                action_vector = agent.predict(input_vector)
                action_index = np.argmax(action_vector)

                self.world.perform_action(agent, action_index)
            time.sleep(0.5)

            # TODO: Do Evolution