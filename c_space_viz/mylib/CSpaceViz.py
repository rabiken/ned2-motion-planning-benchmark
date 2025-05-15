import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mylib.SpecialEuclidean2D import *
from mylib.Rectangle2D import *
from mylib.robotViz import *
from mylib.graph2D import *

class CSpaceViz2D:
    def __init__(self, world: World2D, n_sample=100, min_range = -np.pi, max_range = np.pi):
        self.world = world
        self.min_range = min_range
        self.max_range = max_range
        self.n_sample = n_sample
        robotDof = self.world.robots[0].get_dof()
        if robotDof != 2:
            raise ValueError(f"CSpaceViz2D only supports 2-DOF robot. Robot has {robotDof} DOF.")
    def draw_cspace(self, n_samples=100, min_range = -np.pi, max_range = np.pi):
        self.min_range = min_range
        self.max_range = max_range
        self.n_samples = n_samples
        theta1 = np.linspace(min_range, max_range, n_samples)
        theta2 = np.linspace(min_range, max_range, n_samples)
        theta1_grid, theta2_grid = np.meshgrid(theta1, theta2)
        cspace = np.zeros_like(theta1_grid)

        for i in range(n_samples):
            for j in range(n_samples):
                robot = self.world.robots[0]
                robot.set_link_rotation(0, theta1[j])
                robot.set_link_rotation(1, theta2[i])
                if self.world.check_collision():
                    cspace[i, j] = 1  # Mark as collision

        plt.figure(figsize=(8, 8))
        plt.pcolormesh(theta1, theta2, cspace, shading='auto', cmap='Greys', alpha=0.5)
        collision_patch = patches.Patch(color='gray', label='Obstacle Space')
        free_patch = patches.Patch(color='white', label='Free Space')
        plt.legend(handles=[collision_patch, free_patch], loc='upper right')
        plt.xlabel('Theta1 (rad)')
        plt.ylabel('Theta2 (rad)')
        plt.title('Configuration Space')
        plt.axis('equal')

    def plot_configuration(self, angle1, angle2, name=None):
        # Plot the configuration of the robot in the configuration space
        angle1 = np.clip(angle1, self.min_range, self.max_range)
        angle2 = np.clip(angle2, self.min_range, self.max_range)
        plt.plot(angle1, angle2, 'o', markerfacecolor='white', markeredgecolor='black')
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white", alpha=0.7)
        plt.text(angle1-0.1, angle2, f'{name}: ({angle1:.2f}, {angle2:.2f})', fontsize=9, ha='right', bbox=bbox_props)
    
    def draw_graph(self, graph: Graph2D, node_color='blue', edge_color='gray'):
        # Draw the graph in the configuration space
        graph.draw_graph(node_color=node_color, edge_color=edge_color)