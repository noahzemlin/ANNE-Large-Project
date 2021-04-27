import random
from world import World
from threading import Thread

class SimulationThread(Thread):
    def __init__(self, world: World):
        Thread.__init__(self)

        self.world = world
        self.running = True
    
    def run(self):
        self.exc = None
        
        try:
            while self.running:
                for agent in self.world.agents:
                    info = self.world.agent_info(agent)
                    input_vector = self.world.info_to_vector(info)

                    action = agent.predict(input_vector)

                    self.world.perform_action(agent, action)
        except BaseException as e:
            self.exc = e

    def join(self):
        Thread.join(self)
        if self.exc:
            raise self.exc