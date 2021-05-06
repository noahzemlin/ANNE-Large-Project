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
    def __init__(self, world: World, exp: int):
        RaisingThread.__init__(self)

        self.world = world
        self.running = True
        self.best_agent = None
        self.best_fitness = 0
        self.gen = 0
        self.exp = exp

    def make_agent(self):
        return Agent(3, [3], 3) if self.exp == 3 else Agent(3, [3], 2) # 10 = no pass, 11 = pass

    def run_w_exceptions(self):
        csv_out = open(f"exp_{self.exp}.csv", "w")

        csv_out.write(f"gen,best_exp_{self.exp},median_exp_{self.exp},best_passes_exp_{self.exp},med_passes_exp_{self.exp}\n")

        scores = {g+1:[0,0,0,0] for g in range(300)}

        total_runs = 10
        total_gens = 50

        for _ in range(total_runs):
            # Initalize population
            logging.info("Making Agents")
            self.population = [self.make_agent() for _ in range(80)]
            self.scores = {agent: 0 for agent in self.population}
            self.passes = {agent: 0 for agent in self.population}
            self.gen = 0

            logging.info(f"Architecture: {[(lyr.shape[0]-1, lyr.shape[1]) for lyr in self.population[0].network]}")
            logging.info(f"Number of weights: {sum([lyr.shape[0] * lyr.shape[1] for lyr in self.population[0].network])}")

            for _ in range(total_gens):
                if not self.running:
                    return

                # Run one simulation
                gen, best, med, best_passes, med_passes = self.run_sim()

                # Record results
                scores[gen][0] += best
                scores[gen][1] += med
                scores[gen][2] += best_passes
                scores[gen][3] += med_passes
        
        for gen in range(total_gens):
            best, med, best_passes, med_passes = scores[gen+1]
            csv_out.write(f"{gen+1},{best / total_runs},{med / total_runs},{best_passes / (total_runs):0.2f},{med_passes / (total_runs):0.2f}\n")

        csv_out.close()


    def run_sim(self):

        for i, agent in enumerate(self.population):
            self.world.reset()

            agent_clone = copy.deepcopy(agent)

            self.world.put_agent(agent, 6, 12)
            
            if self.exp == 1:
                agents = [agent]
            else:
                self.world.put_agent(agent_clone, 2, 12)
                agents = [agent, agent_clone]

            # Add 12 objects
            for _ in range(12):
                while not self.world.put_object((random.randint(3, 50), random.randint(3, 8))):
                    # Keep trying to place another object until it places
                    continue

            for _ in range(200):
                self.world.move_num += 1
                for agent_inst in agents:
                    input_vector = self.world.agent_to_vector(agent_inst)

                    action_vector = agent_inst.predict(input_vector)
                    action_index = np.argmax(action_vector)

                    self.world.perform_action(agent_inst, action_index)

            self.scores[agent] = self.world.score

            self.passes[agent] = self.world.num_passes

            agent.age += 1

        # Selection
        random.shuffle(self.population) # Prevent bias
        self.population.sort(key = lambda x: self.scores[x], reverse = True)

        best = self.scores[self.population[0]]
        med = self.scores[self.population[len(self.population)//2]]
        worst = self.scores[self.population[3*len(self.population)//4]]
        best_passes = self.passes[self.population[0]]
        med_passes = self.passes[self.population[len(self.population)//2]]
        logging.info(f"Gen {self.gen} Best: {best:0.02f}, Median: {med:0.02f}, 75th: {worst:0.02f}, Best Passes: {best_passes}, Median Passes: {med_passes}")

        self.best_agent = copy.deepcopy(self.population[0])
        self.best_fitness = best
        self.gen += 1

        if self.gen % 20 == 0:
            with open("agents.pop", "wb") as f:
                pickle.dump(self.population, f)

        # Group parents with tournament selection
        parents = []
        indicies = list(range(len(self.population)))
        for i in range(4):
            sample = random.sample(indicies, len(self.population) // 5)
            sample.sort()
            n = random.randint(0, 1)
            p1, p2 = sample[n], sample[1-n]
            indicies.remove(p1)
            indicies.remove(p2)
            parents.append((self.population[p1], self.population[p2]))

        # Crossover
        children = []
        for pair in parents:
            # Choose random point
            i = random.randint(0, len(pair[0].network)-1)

            # Split among children
            child1 = copy.deepcopy(pair[0])
            child1.network[i:] = copy.deepcopy(pair[1].network[i:])
            child2 = copy.deepcopy(pair[1])
            child2.network[:i] = copy.deepcopy(pair[0].network[:i])

            child1.age = 0
            child2.age = 0

            children.append(child1)
            children.append(child2)

        # Mutation and replacement
        for i, child in enumerate(children):
            # Mutate children
            child.mutate()

            # Replace the worst
            self.population[-(i+1)] = child

        # Kill old farts at random and replace with new agents
        for agent in self.population:
            if agent.age > 10 and random.random() < (agent.age - 10) / 10:
                self.population.remove(agent)
                self.population.append(self.make_agent())

        return self.gen, best, med, best_passes, med_passes