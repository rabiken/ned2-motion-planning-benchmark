import numpy as np
import matplotlib.pyplot as plt
from mylib.Rectangle2D import *
from mylib.SpecialEuclidean2D import *
import matplotlib.animation as animation


class Robot2D:
    def __init__(self, world_frame=None):
        self.links = []  # list of links
        if world_frame is None:
            world_frame = SpecialEuclidean2D()
        self.world_frame = world_frame
    def get_dof(self):
        # Return the number of degrees of freedom of the robot
        return len(self.links)
    def set_world_frame(self, angle, x, y):
        self.world_frame = SpecialEuclidean2D(angle=angle, x=x, y=y)
    def add_link(self, width, height, angle=0.0):
        if len(self.links) == 0:
            # Set the transformation of the new link relative to the previous one
            parent_frame = self.world_frame
        else:
            # Set the transformation of the new link relative to the previous one
            parent_frame = self.links[-1].get_next_frame()
        link = Rectangle2D(width=width, height=height, angle=angle, parent_frame=parent_frame)
        self.links.append(link)
        return link
    def set_link_rotation(self, index, angle):
        if index < 0 or index >= len(self.links):
            raise IndexError(f"Link index {index} out of bounds")
        self.links[index].set_rotation(angle)
        # propagate the transformation to the following links
        for i in range(index + 1, len(self.links)):
            if i == 0: continue
            next_frame = self.links[i-1].get_next_frame()
            self.links[i].set_parent_frame(next_frame)
    def set_configuration(self, config):
        if len(config) != self.get_dof():
            raise ValueError(f"Configuration length {len(config)} does not match robot DOF {self.get_dof()}")
        for i in range(len(config)):
            self.set_link_rotation(i, config[i])
    def set_link_translation(self, index, x, y):
        if index < 0 or index >= len(self.links):
            raise IndexError(f"Link index {index} out of bounds")
        self.links[index].set_translation(x, y)
        for i in range(index + 1, len(self.links)):
            if i == 0: continue
            next_frame = self.links[i-1].get_next_frame()
            self.links[i].set_parent_frame(next_frame)
    def get_link_rotation_angle(self, index):
        if index < 0 or index >= len(self.links):
            raise IndexError(f"Link index {index} out of bounds")
        return self.links[index].get_rotation_angle()
    def get_link_transformation(self, index):
        if index < 0 or index >= len(self.links):
            raise IndexError(f"Link index {index} out of bounds")
        return self.links[index].transformation
    def get_endpoint_in_world_frame(self):
        # Get the endpoint of the last link in the world frame
        endpoint = None
        if len(self.links) == 0:
            endpoint = self.world_frame.get_translation().get_translation_vector()
        else:
            endpoint = self.links[-1].get_next_frame().get_translation().get_translation_vector()
        endpoint = (endpoint[0], endpoint[1])
        return endpoint
    def increment_link_rotation(self, index, delta_angle):
        if index < 0 or index >= len(self.links):
            raise IndexError(f"Link index {index} out of bounds")
        self.set_link_rotation(index=index, angle=self.links[index].get_rotation_angle() + delta_angle)
    def draw_robot(self):
        # Draw the robot on the plot
        for link in self.links:
            link.draw_rectangle()
            link.draw_orientation()
    def get_patches(self, facecolor='blue'):
        # Get the patches for the robot links
        patches = []
        for link in self.links:
            patch = link.get_patch(facecolor=facecolor)
            patches.append(patch)
        return patches

class Obstacle2D(Rectangle2D):
    def __init__(self, width=1.0, height=1.0, angle=0.0, x=0.0, y=0.0):
        super().__init__(width=width, height=height, angle=angle, x=x, y=y)
    def draw_obstacle(self):
        # Draw the obstacle on the plot
        self.draw_rectangle(facecolor='red')
    def check_robot_collision(self, robot: Robot2D) -> bool:
        # Check for collision with the robot
        for link in robot.links:
            if self.check_collision(link):
                return True
        return False
    def get_patch(self):
        # Get the patch for the obstacle
        corners = self.get_corners()
        polygon = plt.Polygon(corners, closed=True, facecolor='red', edgecolor='black', alpha=0.5)
        return polygon

class World2D:
    def __init__(self, xlim=(-20, 20), ylim=(-10, 30)):
        self.robots = []  # list of robots
        self.obstacles = []
        self.fig, self.ax = plt.subplots()
        self.xlim = xlim
        self.ylim = ylim
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.set_aspect('equal', adjustable='box')
        plt.title("Robot Visualization")
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
    def add_robot(self, robot: Robot2D):
        self.robots.append(robot)
    def draw_robots(self):
        # Draw the robots in the world
        for robot in self.robots:
            robot.draw_robot()
    def add_obstacle(self, obstacle: Obstacle2D):
        # Add an obstacle to the world
        self.obstacles.append(obstacle)
    def draw_obstacles(self):
        # Draw the obstacles in the world
        for obstacle in self.obstacles:
            obstacle.draw_obstacle()
    def get_patches(self):
        # Get the patches for the robots and obstacles
        patches = []
        for robot in self.robots:
            patches.extend(robot.get_patches())
        for obstacle in self.obstacles:
            patches.append(obstacle.get_patch())
        return patches
    def check_collision(self):
        # Check for collisions between robots and obstacles
        for robot in self.robots:
            for obstacle in self.obstacles:
                if obstacle.check_robot_collision(robot):
                    return True
        return False
    def draw_world(self):
        # Draw the world with robots and obstacles
        self.draw_obstacles()
        self.draw_robots()

    def animate(self, path, interval=100):
        # Create a new figure and axis for the animation
        fig, ax = plt.subplots()
        self.ax = ax
        self.fig = fig
        self.ax.set_xlim((-25,30))
        self.ax.set_ylim((-10, 30))

        def update(frame):
            # Clear previous frame but avoid clearing the entire figure
            self.ax.clear()
            # Retain plot properties after clearing
            self.ax.set_xlim((-25, 30))
            self.ax.set_ylim((-10, 30))
            self.ax.set_aspect('equal', adjustable='box')
            self.ax.set_title("Robot Visualization")
            self.ax.set_xlabel("X-axis")
            self.ax.set_ylabel("Y-axis")
            
            # Update robot configurations based on the path at the current frame
            robot = self.robots[0]
            robot.set_link_rotation(0, path[frame][0])
            robot.set_link_rotation(1, path[frame][1])

            # Update robot and obstacle patches
            patches = self.get_patches()
            for patch in patches:
                self.ax.add_patch(patch)
            
            return patches

        # Create the animation object
        anim = animation.FuncAnimation(
            self.fig, update, frames=len(path), interval=interval, repeat=False
        )

        # Show the animation
        plt.show()
        return anim

    def show_after_image(self, path, plt_endpoint=True):
        fig, ax = plt.subplots()
        self.ax = ax
        self.fig = fig
        self.ax.set_xlim((-25, 30))
        self.ax.set_ylim((-10, 30))
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title("Robot Visualization")
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")
        # Draw the obstacles
        self.draw_obstacles()
        # Draw the robot
        endpoints_1 = []
        endpoints_2 = []
        for i, config in enumerate(path):
            robot = self.robots[0]
            robot.set_link_rotation(0, config[0])
            robot.set_link_rotation(1, config[1])
            if plt_endpoint:
                endpoint = robot.get_endpoint_in_world_frame()
                endpoints_1.append(endpoint[0])
                endpoints_2.append(endpoint[1])
            # self.draw_robots()
            patches = robot.get_patches()
            for patch in patches:
                self.ax.add_patch(patch)
        if plt_endpoint:
            # Draw the endpoint
            ax.plot(endpoints_1, endpoints_2, '-', color='green', markersize=5, label='Endpoint')
        return fig, ax