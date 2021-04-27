import logging
import numpy as np
from agent import Agent
from structs import AgentInfo, CellType
import curses
import pickle

class World:
    def __init__(self, width: int = 20, height: int = 20):
        self.width = width
        self.height = height
        self.map = [[CellType.FREE for _ in range(height)] for _ in range(width)]

        self.index_to_dir = {}

        i = 0
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    self.index_to_dir[i] = (x,y)
                    i += 1
        
        # Dictionary of agents and their position (x,y) and what they are holding (None if not holding)
        self.agents: dict[Agent, AgentInfo] = {}

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
                return True

            return False
        elif 9 <= action_index <= 16:
            # Pickup/pass
            return True

        return False

    def put_agent(self, agent: Agent, x: int, y: int) -> None:
        self.agents[agent] = AgentInfo(x, y, None)

    def agent_info(self, agent: Agent) -> AgentInfo:
        return self.agents[agent]

    def get_dir_to_nearest_OBJECT(self, start):
        queue = []
        queue.append([start])

        visited = set()

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if self[node] == CellType.OBJECT:
                return path
            
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x != 0 or y != 0:
                        point = (x + node[0], y + node[1])
                        if point not in visited and self.in_map(point) and (self[point] == CellType.FREE or self[point] == CellType.OBJECT):
                            visited.add(point)
                            new_path = list(path)
                            new_path.append(point)
                            queue.append(new_path)
        
        return None

    def info_to_vector(self, agent_info: AgentInfo) -> np.ndarray:
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
        path = self.get_dir_to_nearest_OBJECT((agent_info.x, agent_info.y))
        
        if path is not None:
            dir = (path[1][0] - agent_info.x, path[1][1] - agent_info.y)
        else:
            dir = (0, 0)

        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    look_at = (x, y)
                    if look_at == dir:
                        vector.append(1)
                    else:
                        vector.append(0)

        # Is Holding
        vector.append(1 if agent_info is not None else -1)

        return np.array(vector)

    def from_file(self, filename: str):
        with open(filename, "rb") as f:
            self.width, self.height, self.map = pickle.load(f)

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