import logging
import random
import math
from typing import Any
import numpy as np
from agent import Agent
from structs import AgentInfo, CellType
import pickle
import copy

class Node():
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
        self.move_num = 1
        self.move_num_last_pass = 1
        self.num_passes = 0
        self.objects = []
        
        self.agent_to_target = {}
        self.agent_to_id = {}
        self.agent_last_scored = {}

        i = 0
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x != 0 or y != 0:
                    self.index_to_dir[i] = (x,y)
                    i += 1
        
        # Dictionary of agents and their position (x,y) and what they are holding (None if not holding)
        self.agents: dict[Agent, AgentInfo] = {}
        
        # (cur_pos, goal_pos) -> (dir)
        self.goal_to_dir: dict[Any, Any] = {}

    def add_score(self, agent, value):
        self.score += value

    def attempt_move_agent(self, agent: Agent, info: AgentInfo, delta):
        # Move
        new_pos = (info.x + int(delta[0]), info.y + int(delta[1]))

        # Is another robot on that tile?
        for agent_iter in self.agents:
            if agent_iter == agent:
                continue

            ag_info = self.agents[agent_iter]
            if self.dist((ag_info.x, ag_info.y), new_pos) <= 1.5:
                # Uh oh, too close! Randomly move!
                delta2 = (delta[0], delta[1])

                while delta2 == delta:
                    delta2 = (random.randint(-1, 1), random.randint(-1, 1))
                
                new_pos = (info.x + int(delta2[0]), info.y + int(delta2[1]))
                break

        if self.in_map(new_pos) and self[new_pos] == CellType.FREE:
            self.agents[agent].x = new_pos[0]
            self.agents[agent].y = new_pos[1]
            
            # If agent is near RETURN while holding, unhold and increment score!
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x != 0 or y != 0:
                        point = (x + new_pos[0], y + new_pos[1])
                        if info.holding and self.in_map(point) and self[point] == CellType.RETURN:
                            time_since_last_score = self.move_num - self.agent_last_scored[agent]
                            self.add_score(agent, max(20 - time_since_last_score * 0.2, 1))
                            self.agent_last_scored[agent] = self.move_num

                            # logging.info("Returned object!")
                            self.agents[agent].holding = False
                        if not info.holding and self.in_map(point) and self[point] == CellType.OBJECT:
                            self.add_score(agent, 1)

                            # logging.info("Grabbed object!")
                            self.agents[agent].holding = True

                            self.agent_to_target[agent] = None

                            self.objects.remove(point)
                            self[point] = CellType.FREE
            return True

        return False

    # Attempt to perform an action with a specified agent
    # Returns True on sucess, False otherwise
    # Actions:
    #   0 = No action
    #   1 thru 8 = Move (tl, tc, tp, cl, cc, cr, bl, bc, br)
    #   9 = Move to goal
    def perform_action(self, agent: Agent, action_index = 0):
        info = self.agent_info(agent)

        if action_index == 0:
            # No Action
            return True
        # elif 1 <= action_index <= 8:
        #     # Let them move how they want if they want
        #     delta = self.index_to_dir[action_index - 1]

        #     return self.attempt_move_agent(agent, info, delta)
        elif action_index == 1:
            # Decide goal
            if info.holding:
                goal_pos = (3, 11)
            elif self.agent_to_target[agent] is not None and self[self.agent_to_target[agent]] == CellType.OBJECT:
                # Have a target and its still an object
                goal_pos = self.agent_to_target[agent]
            else:
                # Target doesn't exist

                # Find nearest object and set as target
                smallest_distance = 100000
                self.agent_to_target[agent] = None
                for object in self.objects:
                    dist_to = self.dist(object, (info.x, info.y))
                    if dist_to < smallest_distance:
                        smallest_distance = dist_to
                        self.agent_to_target[agent] = object

                # logging.info(f"Found target: {self.target_object}")

                goal_pos = self.agent_to_target[agent]
            
            if goal_pos == None:
                # Nowhere else to go!
                return True

            # Find dir to goal
            if ((info.x, info.y), goal_pos) in self.goal_to_dir:
                dir = self.goal_to_dir[((info.x, info.y), goal_pos)]
            else:
                path = self.astar((info.x, info.y), goal_pos = goal_pos)
            
                if path is not None and len(path) > 1:
                    dir = (path[1][0] - info.x, path[1][1] - info.y)
                else:
                    logging.info(f"No path to: {goal_pos} from {(info.x, info.y)}")
                    dir = (0, 0)

                self.goal_to_dir[((info.x, info.y), goal_pos)] = dir

            return self.attempt_move_agent(agent, info, dir)
        elif action_index == 2:
            # Pass

            if not info.holding or self.move_num - self.move_num_last_pass <= 4:
                return False

            for pos_agent in self.agents:
                if not pos_agent == agent:
                    pos_info = self.agents[pos_agent]
                    if not pos_info.holding and self.dist((info.x, info.y), (pos_info.x, pos_info.y)) <= 4:
                        self.agents[agent].holding = False
                        self.agents[pos_agent].holding = True

                        self.agent_to_target[agent] = None
                        self.agent_to_target[pos_agent] = None

                        self.move_num_last_pass = self.move_num

                        self.num_passes += 1

        return False

    def put_agent(self, agent: Agent, x: int, y: int) -> None:
        self.agents[agent] = AgentInfo(x, y, None)

        self.agent_to_id[agent] = len(self.agent_to_id)
        self.agent_to_target[agent] = None
        self.agent_last_scored[agent] = 1

    def put_object(self, pos):
        if self[pos] == CellType.FREE:
            self[pos] = CellType.OBJECT
        else:
            return False
        
        self.objects.append(pos)
        return True

    def agent_info(self, agent: Agent) -> AgentInfo:
        return self.agents[agent]

    def reset(self):
        self.map = copy.deepcopy(self.stored_map)
        self.move_num = 1
        self.agents: dict[Agent, AgentInfo] = {}
        self.score = 0
        self.num_passes = 0
        self.move_num_last_score = 1
        self.move_num_last_pass = 1
        self.moves = set()
        self.objects = []
        self.agent_to_target = {}
        self.agent_to_id = {}
        self.agent_last_scored = {}

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
                if self[node_position] == CellType.OBSTACLE:
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

        # Robot nearby
        robot_ready_to_grab = False
        robot_in_range = False
        for pos_agent in self.agents:
            if not pos_agent == agent:
                pos_info = self.agents[pos_agent]
                if not pos_info.holding and self.dist((agent_info.x, agent_info.y), (pos_info.x, pos_info.y)) <= 4:
                    robot_ready_to_grab = True
                if self.dist((agent_info.x, agent_info.y), (pos_info.x, pos_info.y)) <= 2:
                    robot_in_range = True

        vector.append(1 if robot_ready_to_grab else 0)
        vector.append(1 if robot_in_range else 0)

        # Is Holding
        vector.append(1 if agent_info.holding else 0)

        return np.array(vector)

    def dist(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

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