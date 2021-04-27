import logging
import time
from typing import Any
import numpy as np
from agent import Agent
from structs import AgentInfo, CellType
import curses
import pickle
import copy

class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

    def __hash__(self):
        return self.position.__hash__()

class World:
    def __init__(self, width: int = 20, height: int = 20):
        self.width = width
        self.height = height
        self.stored_map = [[CellType.FREE for _ in range(height)] for _ in range(width)]
        self.map = copy.deepcopy(self.stored_map)
        self.index_to_dir = {}
        self.score = 0

        i = 0
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    self.index_to_dir[i] = (x,y)
                    i += 1
        
        # Dictionary of agents and their position (x,y) and what they are holding (None if not holding)
        self.agents: dict[Agent, AgentInfo] = {}
        self.didMove: dict[Agent, bool] = {}
        self.lastDir: dict[Agent, Any] = {}
        
        # (cur_pos, goal_pos) -> (dir)
        self.goal_to_dir: dict[Any, Any] = {}

    # Attempt to perform an action with a specified agent
    # Returns True on sucess, False otherwise
    # Actions:
    #   0 = No action
    #   1 thru 8 = Move (tl, tc, tp, cl, cc, cr, bl, bc, br)
    #   9 thru 16 = Pickup/Pass (^^^)
    def perform_action(self, agent: Agent, action_index = 0):
        info = self.agent_info(agent)

        if action_index == 0:
            # No Action
            return True
        elif 1 <= action_index <= 8:
            # Move
            delta = self.index_to_dir[action_index - 1]
            new_pos = (info.x + int(delta[0]), info.y + int(delta[1]))

            if self.in_map(new_pos) and self[new_pos] == CellType.FREE:
                self.agents[agent].x = new_pos[0]
                self.agents[agent].y = new_pos[1]

                self.score += 0.001
                self.didMove[agent] = True

                # If agent is near RETURN while holding, unhold and increment score!
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        if x != 0 or y != 0:
                            point = (x + new_pos[0], y + new_pos[1])
                            if info.holding and self.in_map(point) and self[point] == CellType.RETURN:
                                self.score += 5
                                logging.info("Returned object!")
                                self.agents[agent].holding = False
                            if not info.holding and self.in_map(point) and self[point] == CellType.OBJECT:
                                self.score += 1
                                logging.info("Grabbed object!")
                                self.agents[agent].holding = True
                                self[point] = CellType.FREE
                return True

            return False
        elif 9 <= action_index <= 16:
            # Pickup/pass
            return True

        return False

    def put_agent(self, agent: Agent, x: int, y: int) -> None:
        self.agents[agent] = AgentInfo(x, y, None)
        self.didMove[agent] = True
        self.lastDir[agent] = (0, 0)

    def agent_info(self, agent: Agent) -> AgentInfo:
        return self.agents[agent]

    def reset(self):
        self.map = copy.deepcopy(self.stored_map)
        self.agents: dict[Agent, AgentInfo] = {}
        self.score = 0

    # THIS IS SO SLOW PLEASE FIX IT
    # THIS IS LITERALLY O(N^2) BREATH FIRST SEARCH AHHHHHH
    def get_dir_to_nearest_goal(self, start, goal=CellType.OBJECT):
        queue = []
        queue.append([start])

        visited = set()

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if self[node] == goal:
                return path
            
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x != 0 or y != 0:
                        point = (x + node[0], y + node[1])
                        if point not in visited and self.in_map(point) and (self[point] == CellType.FREE or self[point] == goal):
                            visited.add(point)
                            new_path = list(path)
                            new_path.append(point)
                            queue.append(new_path)
        
        return None

    def astar(self, start, goal_pos, goal=CellType.OBJECT):
        """Returns a list of tuples as a path from the given start to the given end in the given maze"""



        # Create start and end node
        start_node = Node(None, start)
        start_node.g = start_node.h = start_node.f = 0
        end_node = Node(None, goal_pos)
        end_node.g = end_node.h = end_node.f = 0

        # Initialize both open and closed list
        open_list = set()
        closed_list = set()

        # Add the start node
        open_list.add(start_node)
        adj = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # Loop until you find the end
        count = 0
        while len(open_list) > 0:
            count += 1
            # Get the current node
            current_node = min(open_list, key=lambda x: x.f)

            # Pop current off open list, add to closed list
            open_list.remove(current_node)
            closed_list.add(current_node)

            # Found the goal
            if current_node == end_node:
                path = []
                current = current_node
                while current is not None:
                    path.append(current.position)
                    current = current.parent
                return path[::-1] # Return reversed path

            # Generate children
            children = []
            for new_position in adj: # Adjacent squares

                # Get node position
                node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

                # Make sure within range
                if not self.in_map(node_position):
                    continue

                # Make sure walkable terrain
                if not (self[node_position] == CellType.FREE or self[node_position] == goal):
                    continue

                # Create new node
                new_node = Node(current_node, node_position)

                # Append
                children.append(new_node)

            # Loop through children
            for child in children:

                # Child is on the closed list
                if child in closed_list:
                    continue

                # Create the f, g, and h values
                child.g = current_node.g + 1
                child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
                child.f = child.g + child.h

                # Child is already in the open list
                if child in open_list:
                    for obj in open_list:
                        if child == obj:
                            break
                    if child.g >= obj.g:
                        continue

                # Add the child to the open list
                open_list.add(child)

    def agent_to_vector(self, agent: Agent) -> np.ndarray:
        agent_info = self.agent_info(agent)
        vector = []

        # Free spaces
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    look_at = (agent_info.x + x, agent_info.y + y)
                    if self.in_map(look_at):
                        vector.append(1 if self[look_at] == CellType.FREE else 0)
                    else:
                        vector.append(0)

        # Robot spaces
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    look_at = (agent_info.x + x, agent_info.y + y)
                    if self.in_map(look_at):
                        vector.append(1 if self[look_at] == CellType.ROBOT else 0)
                    else:
                        vector.append(0)

        # Best path to nearest object if not holding, return point if holding
        if agent_info.holding:
            goal_pos = (3, 12)
        else:
            goal_pos = (3, 6)

        if self.didMove[agent]:
            if ((agent_info.x, agent_info.y), goal_pos) in self.goal_to_dir:
                dir = self.goal_to_dir[((agent_info.x, agent_info.y), goal_pos)]
            else:
                path = self.astar((agent_info.x, agent_info.y), goal_pos = goal_pos, goal=CellType.OBJECT if agent_info.holding is None else CellType.RETURN)
            
                if path is not None:
                    dir = (path[1][0] - agent_info.x, path[1][1] - agent_info.y)
                else:
                    dir = (0, 0)

                self.lastDir[agent] = dir
                self.goal_to_dir[((agent_info.x, agent_info.y), goal_pos)] = dir
                self.didMove[agent] = False
        else:
            dir = self.lastDir[agent]

        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    look_at = (x, y)
                    if look_at == dir:
                        vector.append(1)
                    else:
                        vector.append(0)

        # Is Holding
        vector.append(1 if agent_info.holding is not None else -1)

        return np.array(vector)

    def from_file(self, filename: str):
        with open(filename, "rb") as f:
            self.width, self.height, self.stored_map = pickle.load(f)
            self.reset()

    def to_file(self, filename: str):
        with open(filename, "wb") as f:
            pickle.dump((self.width, self.height, self.map), f)

    def in_map(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] <= self.height

    def __getitem__(self, pos):
        if self.in_map(pos):
            x,y = pos
            return self.map[x][y]
        else:
            raise Exception(f"{pos} not in map with bounds {self.width, self.height}")

    def __setitem__(self, pos, val):
        if self.in_map(pos):
            x,y = pos
            self.map[x][y] = val
        else:
            raise Exception(f"{pos} not in map with bounds {self.width, self.height}")