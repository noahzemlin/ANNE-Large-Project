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
        
        # Dictionary of agents and their position (x,y) and what they are holding (None if not holding)
        self.agents = {}

    # Attempt to perform an action with a specified agent
    # Returns TRUE on sucess, FALSE otherwise
    def perform_action(self, agent: Agent, action: np.ndarray):
        pass

    def put_agent(self, agent: Agent, x: int, y: int) -> None:
        self.agents[agent] = AgentInfo(x, y, None)

    def agent_info(self, agent: Agent) -> AgentInfo:
        return self.agents[agent]

    def info_to_vector(self, agent_info: AgentInfo):
        return np.array([0, 1, 2, 1 if agent_info is not None else -1])

    def from_file(self, filename: str):
        with open(filename, "rb") as f:
            self.width, self.height, self.map = pickle.load(f)

    def to_file(self, filename: str):
        with open(filename, "wb") as f:
            pickle.dump((self.width, self.height, self.map), f)

    def __getitem__(self, pos):
        x,y = pos
        return self.map[x][y]

    def __setitem__(self, pos, val):
        x,y = pos
        self.map[x][y] = val