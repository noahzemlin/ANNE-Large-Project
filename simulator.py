import copy
import pickle
from numpy.lib.function_base import median
from agent import Agent
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
        self.best_agent = None
        self.best_fitness = 0
        self.gen = 0

    def make_agent(self):
        return Agent(3, [6], 11)

    def run_w_exceptions(self):
        # Initalize population
        logging.info("Making Agents")
        self.population = [self.make_agent() for _ in range(120)]
        self.scores = {agent: 0 for agent in self.population}

        logging.info(f"Number of weights: {sum([lyr.shape[0] * lyr.shape[1] for lyr in self.population[0].network])}")

        while self.running:
            # Run one simulation
            for i, agent in enumerate(self.population):
                if not self.running:
                    return
                self.world.reset()

                agent_clone = copy.deepcopy(agent)

                self.world.put_agent(agent, 4, 12)
                self.world.put_agent(agent_clone, 2, 12)

                self.world.put_object((random.randint(3, 50), random.randint(3, 8)))

                agents = [agent, agent_clone]

                # Add 4 more objects
                for _ in range(6):
                    while not self.world.put_object((random.randint(3, 35), random.randint(3, 8))):
                        # Keep trying to place second object until it places
                        continue

                for _ in range(160):
                    for agent_inst in agents:
                        input_vector = self.world.agent_to_vector(agent_inst)

                        action_vector = agent_inst.predict(input_vector)
                        action_index = np.argmax(action_vector)

                        self.world.perform_action(agent_inst, action_index)

                self.scores[agent] = self.world.score

            # Selection
            random.shuffle(self.population) # Prevent bias
            self.population.sort(key = lambda x: self.scores[x], reverse = True)

            best = self.scores[self.population[0]]
            med = self.scores[self.population[len(self.population)//2]]
            worst = self.scores[self.population[3*len(self.population)//4]]
            logging.info(f"Gen {self.gen} Best: {best:0.02f}, Median: {med:0.02f}, 75th: {worst:0.02f}")

            self.best_agent = copy.deepcopy(self.population[0])
            self.best_fitness = best
            self.gen += 1

            if self.gen % 20 == 0:
                with open("agents.pop", "wb") as f:
                    pickle.dump(self.population, f)

            samples = list(range(30)) # Sample from top 30
            random.shuffle(samples)
            parents = [(self.population[samples[i]], self.population[samples[i+1]]) for i in range(0, 11, 2)] # Create 6 pairs
            children = []

            # Crossover
            for pair in parents:
                # Choose random point
                i = random.randint(0, len(pair[0].network)-1)

                # Split among children
                child1 = copy.deepcopy(pair[0])
                child1.network[i:] = copy.deepcopy(pair[1].network[i:])
                child2 = copy.deepcopy(pair[1])
                child2.network[:i] = copy.deepcopy(pair[0].network[:i])

                children.append(child1)
                children.append(child2)

            # Mutation and replacement
            for i, child in enumerate(children):
                # Layer to mutate
                layer_i = random.randint(0, len(child.network)-1)
                shape = child.network[layer_i].shape
                adj_mask = np.random.random(size=shape) > 0.7
                repl_mask = np.random.random(size=shape) > 0.9

                child.network[layer_i][adj_mask] += np.random.normal(0, 0.1, shape)[adj_mask]
                child.network[layer_i][repl_mask] = np.random.normal(0, 0.4, shape)[repl_mask]

                # Replace starting from 6th worst
                self.population[-(i+6)] = child

                # Recreate worst 5 for diversity sake
                self.population[-5:] = [self.make_agent() for _ in range(5)]