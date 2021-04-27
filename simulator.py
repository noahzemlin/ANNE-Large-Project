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

    def run_w_exceptions(self):
        # Initalize population
        logging.info("Making Agents")
        self.population = [Agent(8 * 3 + 1, [], 8 * 2 + 1) for _ in range(140)]
        self.scores = {agent: 0 for agent in self.population}

        gen = 0
        while self.running:
            # Run one simulation
            for i, agent in enumerate(self.population):
                if not self.running:
                    return
                self.world.reset()
                self.world.put_agent(agent, 2, self.world.height//3 * 2)

                for _ in range(60):
                    input_vector = self.world.agent_to_vector(agent)

                    action_vector = agent.predict(input_vector)
                    action_index = np.argmax(action_vector)

                    # Reward going towards goal
                    if action_index == np.argmax(input_vector[16:25]) + 1:
                        self.world.score += 0.05

                    self.world.perform_action(agent, action_index)

                self.scores[agent] = self.world.score

            # Selection
            random.shuffle(self.population) # Prevent bias
            self.population.sort(key = lambda x: self.scores[x], reverse = True)

            best = self.scores[self.population[0]]
            med = self.scores[self.population[len(self.population)//2]]
            worst = self.scores[self.population[-11]]
            logging.info(f"Gen {gen} Best: {best:0.02f}, Median: {med:0.02f}, Worst: {worst:0.02f}")

            gen += 1

            if gen % 20 == 0:
                with open("agents.pop", "wb") as f:
                    pickle.dump(self.population, f)

            samples = list(range(10))
            random.shuffle(samples)
            parents = [(self.population[samples[i]], self.population[samples[i+1]]) for i in range(0, 9, 2)]
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

                child.network[layer_i][adj_mask] += np.random.normal(0, 0.05, shape)[adj_mask]
                child.network[layer_i][repl_mask] = np.random.normal(0, 0.4, shape)[repl_mask]

                # Replace 20-10
                self.population[-(i+11)] = child

                # Recreate worst 10 for diversity sake
                self.population[-10:] = [Agent(8 * 3 + 1, [24, 16], 8 * 2 + 1) for _ in range(10)]