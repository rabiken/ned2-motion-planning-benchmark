import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mylib.SpecialEuclidean2D import *
from mylib.Rectangle2D import *
from mylib.robotViz import *
from mylib.graph2D import *
# from mylib.CSpaceViz import *

class MotionPlanner2D:
    def __init__(self, robot: Robot2D, obstacles: list, start: tuple, goal: tuple, joint_limit=(-np.pi, np.pi)):
        self.joint_limit = joint_limit
        self.robot = robot
        self.obstacles = obstacles
        self.start = start
        self.goal = goal
        self.collision_checker = CollisionChecker()
    
    def check_collision(self):
        # Check for collision with obstacles
        for obstacle in self.obstacles:
            if obstacle.check_robot_collision(self.robot):
                return True
        return False
    def is_valid_config(self, config):
        # Check if the configuration is within joint limits
        for angle in config:
            if angle < self.joint_limit[0] or angle > self.joint_limit[1]:
                return False
        # Set the robot configuration
        self.robot.set_link_rotation(0, config[0])
        self.robot.set_link_rotation(1, config[1])
        # Check for collision
        if self.check_collision():
            return False    
        return True
    
    def check_edge(self, node1, node2)-> bool:
        return True
    
    def is_valid_edge(self, q1: tuple, q2: tuple):
        # Check if the edge between q1 and q2 is valid
        path = self.interpolate(q1, q2)
        for point in path:
            if not self.is_valid_config(point):
                return False
        return True
    
    
    def interpolate(self, start, goal):
        # Interpolate between two configurations
        # print start and goal
        # print(f"Interpolating between {start} and {goal}")
        dist = np.linalg.norm(np.array(goal) - np.array(start))
        steps = int(dist / self.min_dist)
        if steps == 0:
            return [start, goal]  # no interpolation needed
        path = []
        for i in range(steps + 1):
            alpha = float(i) / float(steps)
            point0 = (1 - alpha) * start[0] + alpha * goal[0]
            point1 = (1 - alpha) * start[1] + alpha * goal[1]
            point = (point0, point1)
            path.append(point)
        return path
    
    def build_graph(self, n_samples=20)-> bool:
        graph = Graph2D()
        for i in range(n_samples):
            angle1 = np.random.uniform(self.joint_limit[0], self.joint_limit[1])
            angle2 = np.random.uniform(self.joint_limit[0], self.joint_limit[1])
            if self.is_valid_config((angle1, angle2)):
                print(f"Adding node: {angle1}, {angle2}")
                graph.add_node((angle1, angle2))
        
        for node1 in graph.nodes:
            for node2 in graph.nodes:
                if node1 != node2 and self.check_edge(node1, node2):
                    graph.add_edge(node1, node2)
        
        self.graph = graph
        return True
    def get_graph(self):
        return self.graph
    
    def grow_graph(self, n_samples=20):
        pass
        
    def plan(self, n_samples=500):
        # Build the graph
        success = self.build_graph(n_samples=n_samples)
        if not success:
            print("Failed to find a path")
            return None, None
        # Run Dijkstra's algorithm
        dijkstra = Dijkstra(self.graph, self.start, self.goal)
        path, cost = dijkstra.find_shortest_path()
        return path, cost
    
    
class RRTPlanner2D(MotionPlanner2D):
    def __init__(self, robot: Robot2D, obstacles: list, start: tuple, goal: tuple, joint_limit=(-np.pi, np.pi), step_size=0.1, goal_bias=0.05):
        self.step_size = step_size
        self.min_dist = 0.1
        self.goal_bias = goal_bias
        super().__init__(robot=robot, obstacles=obstacles, start=start, goal=goal, joint_limit=joint_limit)
        self.graph = Graph2D()
    
    def extend_rrt(self, q: tuple):
        q_near = self.graph.sample_nearest(q)
        direction = np.array(q) - np.array(q_near)
        if np.linalg.norm(direction) < self.step_size:
            q_new = q_near + direction
        else:
            direction /= np.linalg.norm(direction)
            q_new = q_near + self.step_size * direction
        if self.is_valid_config(q_new) and self.is_valid_edge(q_near, q_new):
            self.graph.add_node((q_new[0], q_new[1]))
            self.graph.add_edge(q_near, q_new)
            return q_new
        return None
    
    def close_to_goal(self, q: tuple):
        # Check if the node is close to the goal
        return np.linalg.norm(np.array(q) - np.array(self.goal)) <= self.step_size

    def get_random_config(self):
        # Generate a random configuration within the joint limits with goal bias
        if np.random.rand() < self.goal_bias:
            q_rand = self.goal
        else:
            q_rand = np.random.uniform(self.joint_limit[0], self.joint_limit[1], size=2)
        return tuple(q_rand)

    def grow_graph(self, n_samples=20):
        for i in range(n_samples):
            q_rand = self.get_random_config()
            q_rand = tuple(q_rand)
            q_new = self.extend_rrt(q_rand)
            if q_new is not None and self.close_to_goal(q_new) and self.is_valid_edge(q_new, self.goal):
                self.graph.add_node(self.goal)
                self.graph.add_edge(q_new, self.goal)
                print(f"Goal reached: {self.goal}")
                return True
        return False        

    def build_graph(self, n_samples=2000):
        self.graph.add_node(self.start)
        found = False
        for i in range(n_samples):
            q_rand = self.get_random_config()
            q_rand = tuple(q_rand)
            q_new = self.extend_rrt(q_rand)
            if q_new is not None and self.close_to_goal(q_new) and self.is_valid_edge(q_new, self.goal):
                self.graph.add_node(self.goal)
                self.graph.add_edge(q_new, self.goal)
                print(f"Goal reached: {self.goal} at iteration {i}")
                found = True
        return found

class ESTPlanner2D(MotionPlanner2D):
    def __init__(self, robot: Robot2D, obstacles: list, start: tuple, goal: tuple, joint_limit=(-np.pi, np.pi), step_size=0.5, goal_bias=0.05):
        self.step_size = step_size
        self.min_dist = 0.1
        self.nbhood_radius = step_size / 3
        self.goal_bias = goal_bias
        super().__init__(robot=robot, obstacles=obstacles, start=start, goal=goal, joint_limit=joint_limit)
        self.graph = Graph2D()
        self.neigh_cnt = np.zeros((int(2 * np.pi / self.nbhood_radius)+1, int(2 * np.pi / self.nbhood_radius)+1))
        # self.neigh_cnt = dict[tuple[int,int], int]()
    
    def get_grid_key(self, q: tuple):
        # Convert the configuration to a grid key
        return (int( (q[0]+np.pi)  / self.nbhood_radius), int( (q[1]+np.pi) / self.nbhood_radius))
    def update_neigh_cnt(self, q: tuple):
        key = self.get_grid_key(q)
        self.neigh_cnt[key[0], key[1]] += 1.0
        for shift1 in range(-1, 2):
            for shift2 in range(-1, 2):
                if shift1 == 0 and shift2 == 0:
                    continue
                key2 = (key[0] + shift1, key[1] + shift2)
                if key2[0] < 0 or key2[0] >= self.neigh_cnt.shape[0] or key2[1] < 0 or key2[1] >= self.neigh_cnt.shape[1]:
                    continue
                self.neigh_cnt[key2[0], key2[1]] += 0.1
        return self.neigh_cnt[key[0], key[1]]
    def select_node_with_probability(self):
        # grid = np.zeros((self.neigh_cnt.shape[0], self.neigh_cnt.shape[1]))
        probabilities = np.zeros((self.neigh_cnt.shape[0], self.neigh_cnt.shape[1]))
        for i in range(self.neigh_cnt.shape[0]):
            for j in range(self.neigh_cnt.shape[1]):
                cnt = self.neigh_cnt[i, j]
                if cnt == 0:
                    # grid[i, j] = 1e100
                    probabilities[i, j] = 0
                else:
                    # grid[i, j] = self.neigh_cnt[i, j]
                    probabilities[i, j] = 1/cnt ** 2 # make the weights more distinct
        # Normalize the probabilities
        probabilities = probabilities / np.sum(probabilities)
        # inv_densities =  grid  # avoid div-by-zero
        # probabilities = inv_densities / np.sum(inv_densities)
        probabilities = probabilities.flatten()
        selected_idx = np.random.choice(len(probabilities), p=probabilities)
        selected_idx = (selected_idx // self.neigh_cnt.shape[1], selected_idx % self.neigh_cnt.shape[1])
        selected_node = (selected_idx[0] * self.nbhood_radius - np.pi, selected_idx[1] * self.nbhood_radius - np.pi)
        # print(f'selected cell: {selected_node}')
        selected_node = self.graph.sample_nearest(selected_node)
        # print(f'selected node: {selected_node}')
        return selected_node

    def get_random_collision_free_neighbor(self, q: tuple):
        if np.random.rand() < self.goal_bias:
            goal_direction = np.array(self.goal) - np.array(q)
            goal_direction /= np.linalg.norm(goal_direction)
            scale = np.random.uniform(0, 1)
            q_new_0 = q[0] + self.step_size * goal_direction[0] * scale
            q_new_1 = q[1] + self.step_size * goal_direction[1] * scale
            q_new = (q_new_0, q_new_1)
            # Check if the new configuration is valid
            if self.is_valid_config(q_new):
                return q_new
        # Get a random neighbor of q that is collision-free
        q_new_list = []
        prob_list = []
        for i in range(3):
            q_rand = np.random.randn(2)
            q_rand /= np.linalg.norm(q_rand)
            scale = np.random.uniform(0, 1)
            q_new_0 = q[0] + self.step_size * q_rand[0] * scale
            q_new_1 = q[1] + self.step_size * q_rand[1] * scale
            q_new = (q_new_0, q_new_1)
            if self.is_valid_config(q_new):
                key = self.get_grid_key(q_new)
                weight = self.neigh_cnt[key[0], key[1]] + 1e-3  # avoid div-by-zero
                prob = 1 / weight ** 2
                q_new_list.append(q_new)
                prob_list.append(prob)
        if len(q_new_list) == 0:
            return None
        prob_list = np.array(prob_list)
        prob_list /= np.sum(prob_list)
        selected_idx = np.random.choice(len(prob_list), p=prob_list)
        q_new = q_new_list[selected_idx]
        return q_new


    def close_to_goal(self, q: tuple):
        # Check if the node is close to the goal
        return np.linalg.norm(np.array(q) - np.array(self.goal)) <= self.step_size


    def extend_est(self, q: tuple):
        q_new = self.get_random_collision_free_neighbor(q)
        if q_new is None:
            return None
        if self.is_valid_edge(q, q_new):
            self.update_neigh_cnt(q_new)
            self.graph.add_node((q_new[0], q_new[1]))
            self.graph.add_edge(q, q_new)
            return q_new
        return None
    
    def init_planner(self):
        self.graph.add_node(self.start)
        self.update_neigh_cnt(self.start)
    
    def grow_graph(self, n_samples=20):
        found = False
        for i in range(n_samples):
            q_selected = self.select_node_with_probability()
            q_new = self.extend_est(q_selected)
            if q_new is not None and self.close_to_goal(q_new):
                self.graph.add_node(self.goal)
                self.update_neigh_cnt(self.goal)
                self.graph.add_edge(q_new, self.goal)
                found = True
                print(f"Goal reached: {self.goal} at iteration {i}")
        return found
        
        
    def build_graph(self, n_samples=2000):
        self.graph.add_node(self.start)
        self.update_neigh_cnt(self.start)
        return self.grow_graph(n_samples=n_samples)
        

class PRMPlanner2D(MotionPlanner2D):
    def __init__(self, robot: Robot2D,
                  obstacles: list, 
                  start: tuple, 
                  goal: tuple, 
                  joint_limit=(-np.pi, np.pi), 
                #   step_size=0.5, 
                #   goal_bias=0.05,
                  k_nearest=5):
        self.k_nearest = k_nearest
        # self.step_size = step_size
        self.min_dist = 0.1
        # self.goal_bias = goal_bias
        super().__init__(robot=robot, obstacles=obstacles, start=start, goal=goal, joint_limit=joint_limit)
        self.graph = Graph2D()
    
    def get_random_config(self):
        # Generate a random configuration within the joint limits with goal bias
        q_rand = np.random.uniform(self.joint_limit[0], self.joint_limit[1], size=2)
        return tuple(q_rand)
    
    # The time complexity of this function can be reduced to O(log n) using KDTree or BallTree
    # However, for simplicity, we will use a brute-force approach here,
    # which is O(n) time complexity
    # where n is the number of nodes in the graph
    def get_k_nearest(self, q: tuple, k=None, remove_self=True):
        # Get the k nearest nodes to q
        if k is None:
            k = self.k_nearest
        if remove_self:
            k += 1
        distances = []
        for node in self.graph.nodes:
            distance = np.linalg.norm(np.array(node) - np.array(q))
            distances.append((node, distance))
        distances.sort(key=lambda x: x[1])
        if remove_self:
            return [node for node, _ in distances[1:k]]
        return [node for node, _ in distances[:k]]
    
    def build_graph(self, n_samples=2000):
        while len(self.graph.nodes) < n_samples:
            q_rand = self.get_random_config()
            q_rand = tuple(q_rand)
            if self.is_valid_config(q_rand):
                self.graph.add_node(q_rand)
        for node1 in self.graph.nodes:
            k_nearest = self.get_k_nearest(node1, remove_self=True)
            for node2 in k_nearest:
                if self.is_valid_edge(node1, node2):
                    self.graph.add_edge(node1, node2)
            
    def add_start_n_goal_to_graph(self, start: tuple, goal: tuple):
        self.graph.add_node(start)
        self.graph.add_node(goal)
        N_q_init = self.get_k_nearest(start)
        N_q_goal = self.get_k_nearest(goal)
        q_init_closest = None
        for q in N_q_init:
            if self.is_valid_edge(start, q):
                q_init_closest = q
                break
        if q_init_closest is None:
            print("No valid edge found from start to graph")
            return None
        self.graph.add_edge(start, q_init_closest)
        q_goal_closest = None
        for q in N_q_goal:
            if self.is_valid_edge(goal, q):
                q_goal_closest = q
                break
        if q_goal_closest is None:
            print("No valid edge found from goal to graph")
            return None
        self.graph.add_edge(goal, q_goal_closest)
        
    def plan(self, n_samples=2000):
        # Build the graph
        self.build_graph(n_samples=n_samples)
        # Add start and goal to the graph
        self.add_start_n_goal_to_graph(self.start, self.goal)
        # Run Dijkstra's algorithm
        dijkstra = Dijkstra(self.graph, self.start, self.goal)
        path, cost = dijkstra.find_shortest_path()
        return path, cost


