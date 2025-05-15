import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mylib.SpecialEuclidean2D import *
from mylib.Rectangle2D import *
from mylib.robotViz import *
from mylib.graph2D import *
# from mylib.CSpaceViz import *

class Graph2D:
    def __init__(self, path=None):
        self.nodes = []
        self.edges = {}
        if isinstance(path, list):
            self.add_node(path[0])
            for i, node in enumerate(path):
                if i == 0:
                    continue
                self.add_node(node)
                self.add_edge(path[i-1], node)
        elif path is not None:
            raise ValueError("Path must be a list of nodes.")

    def add_node(self, node):
        node = tuple(node)  # Ensure node is hashable
        self.nodes.append(node)
        self.edges[node] = []
    
    def add_edge(self, node1, node2):
        node1 = tuple(node1)  # Ensure node is hashable
        node2 = tuple(node2)
        if node1 in self.nodes and node2 in self.nodes:
            # print(f"Adding edge: {node1} <-> {node2}")
            self.edges[node1].append(node2)
            self.edges[node2].append(node1)
        # else:
        #     print(f"Cannot add edge, one or both nodes not in graph: {node1}, {node2}")
        #     print(f'closest node: {self.sample_nearest(node1)}')
        #     print(f'closest node: {self.sample_nearest(node2)}')
    def draw_graph(self, node_color='blue', edge_color='gray', markersize=3):
        for node in self.nodes:
            for neighbor in self.edges[node]:
                plt.plot([node[0], neighbor[0]], [node[1], neighbor[1]], color=edge_color, linestyle='-', alpha=0.5)
        for node in self.nodes:
            plt.plot(node[0], node[1], 'o', color=node_color, markersize=markersize)
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.title('Graph Visualization')
        plt.axis('equal')
        plt.grid()

    # By using structures like KDTree or BallTree, we can speed up the nearest neighbor search
    # upto O(log n) time complexity
    # However, for simplicity, we will use a brute-force approach here,
    # which is O(n) time complexity
    # where n is the number of nodes in the graph
    def sample_nearest(self, q):
        # Find the nearest node in the graph to the given point q
        nearest_node = None
        min_distance = float('inf')
        for node in self.nodes:
            distance = np.linalg.norm(np.array(node) - np.array(q))
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        return nearest_node
    

class Dijkstra:
    def __init__(self, G: 'Graph2D', start: tuple, goal: tuple):
        self.G = G
        self.start = start
        self.goal = goal
        self.visited = set()
        self.parent = {}
        self.cost = {}
    def calc_cost(self, node1, node2):
        # Calculate the cost between two nodes
        return np.linalg.norm(np.array(node1) - np.array(node2))
    def reconstruct_path(self):
        # Reconstruct the path from start to goal
        path = []
        current_node = self.goal
        while current_node is not None:
            path.append(current_node)
            current_node = self.parent.get(current_node)
        path.reverse()
        return path
    def find_shortest_path(self):
        self.cost[self.start] = 0.0
        self.parent[self.start] = None
        Q = [(0.0, self.start)]
        while len(Q) > 0:
            current_cost, current_node = min(Q, key=lambda x: x[0])
            Q.remove((current_cost, current_node))
            if current_node == self.goal:
                break
            self.visited.add(current_node)
            for neighbor in self.G.edges[current_node]:
                new_cost = current_cost + self.calc_cost(current_node, neighbor)
                if neighbor not in self.cost or new_cost < self.cost[neighbor]:
                    self.cost[neighbor] = new_cost
                    self.parent[neighbor] = current_node
                    Q.append((new_cost, neighbor))

        return self.reconstruct_path(), self.cost[self.goal] if self.goal in self.cost else float('inf')

class AStar:
    def __init__(self, G: 'Graph2D', start: tuple, goal: tuple):
        self.G = G
        self.start = start
        self.goal = goal
        self.visited = set()
        self.parent = {}
        self.g_cost = {}
        self.f_cost = {}
        self.g_cost[self.start] = 0
        self.f_cost[self.start] = self.heuristic(self.start, self.goal)
        self.parent[self.start] = None
    def calc_cost(self, node1, node2):
        # Heuristic function (Euclidean distance)
        return np.linalg.norm(np.array(node1) - np.array(node2))
    def reconstruct_path(self):
        # Reconstruct the path from start to goal
        path = []
        current_node = self.goal
        while current_node is not None:
            path.append(current_node)
            current_node = self.parent.get(current_node)
        path.reverse()
        return path
    def find_shortest_path(self):
        Q = [(self.f_cost[self.start], self.start)]
        while len(Q) > 0:
            current_f_cost, current_node = min(Q, key=lambda x: x[0])
            Q.remove((current_f_cost, current_node))
            if current_node == self.goal:
                break
            self.visited.add(current_node)
            for neighbor in self.G.edges[current_node]:
                new_g_cost = self.g_cost[current_node] + self.calc_cost(current_node, neighbor)
                if neighbor not in self.g_cost or new_g_cost < self.g_cost[neighbor]:
                    self.g_cost[neighbor] = new_g_cost
                    self.f_cost[neighbor] = new_g_cost + self.heuristic(neighbor, self.goal)
                    self.parent[neighbor] = current_node
                    Q.append((self.f_cost[neighbor], neighbor))
        return self.reconstruct_path(), self.g_cost[self.goal] if self.goal in self.g_cost else float('inf')