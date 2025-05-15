import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mylib.SpecialEuclidean2D import *

class CollisionChecker:
    def project_onto_axis(self, corners, axis):
        # Project the corners onto the axis and return the min and max values
        projections = [np.dot(corner, axis) for corner in corners]
        return min(projections), max(projections)
    def check_collision(self, corners1, corners2):
        # Check for collision between two rectangles
        # Using Separating Axis Theorem (SAT)
        axes = []
        for corners in [corners1, corners2]:
            for i in range(2):
                p1 = corners[i]
                p2 = corners[(i + 1) % len(corners)]
                edge = np.array(p2) - np.array(p1)
                axis = edge / np.linalg.norm(edge)
                axes.append(axis)
        for axis in axes:
            min1, max1 = self.project_onto_axis(corners1, axis)
            min2, max2 = self.project_onto_axis(corners2, axis)
            if max1 < min2 or max2 < min1:
                return False
        return True
    def __call__(self, corners1, corners2):
        return self.check_collision(corners1, corners2)

class Rectangle2D:
    def __init__(self, width=1.0, height=1.0, angle=0.0, x=0.0, y=0.0, parent_frame=None):
        self.width = width
        self.height = height
        self.transformation = SpecialEuclidean2D(angle=angle, x=x, y=y)
        if parent_frame is None:
            parent_frame = SpecialEuclidean2D()
        self.parent_frame = parent_frame
        self.next_frame = None
        self.update_next_frame()
    def set_transformation(self, angle, x, y):
        self.transformation.set_rotation(angle)
        self.transformation.set_translation(x, y)
        self.update_next_frame()
    def set_rotation(self, angle):
        self.transformation.set_rotation(angle)
        self.update_next_frame()
    
    def get_rotation_angle(self):
        return self.transformation.rotation.get_angle()
    def set_translation(self, x, y):
        self.transformation.set_translation(x, y)
        self.update_next_frame()
    def set_parent_frame(self, parent_frame):
        # Set the parent frame for the rectangle
        self.parent_frame = parent_frame
        self.update_next_frame()
    def get_parent_frame(self):
        return self.parent_frame
    def update_next_frame(self):
        translateion = SpecialEuclidean2D(x=0, y=self.height, angle=0)
        new_frame = self.parent_frame @ self.transformation @ translateion
        self.next_frame = new_frame
        return self.next_frame
    def get_next_frame(self):
        # Get the next frame in the hierarchy
        return self.next_frame
    def get_corners(self):
        # Get the corners of the rectangle in local coordinates
        half_width = self.width / 2
        corners = np.array([[-half_width, 0],
                            [ half_width, 0],
                            [ half_width, self.height],
                            [-half_width, self.height]])
        # Apply the transformation to the corners
        Tr = self.parent_frame.get_transformation_matrix() @ self.transformation.get_transformation_matrix()
        corners_homogeneous = np.hstack((corners, np.ones((corners.shape[0], 1))))
        transformed_corners = (Tr @ corners_homogeneous.T)[0:2, :]
        return [(transformed_corners[0,i], transformed_corners[1,i]) for i in range(transformed_corners.shape[1])]

    def check_collision(self, other: 'Rectangle2D') -> bool:
        # Check for collision with another rectangle
        corners_self = self.get_corners()
        corners_other = other.get_corners()
        return CollisionChecker().check_collision(corners_self, corners_other)
    def draw_rectangle(self, facecolor=None):
        # Draw the rectangle on the plot
        corners = self.get_corners()
        polygon = patches.Polygon(corners, closed=True, fill=True, edgecolor='black', facecolor=facecolor, alpha=0.5)
        plt.gca().add_patch(polygon)
        plt.gca().set_aspect('equal', adjustable='box')
    def get_patch(self, facecolor=None):
        # Get the patches for the rectangle
        corners = self.get_corners()
        polygon = patches.Polygon(corners, closed=True, fill=True, edgecolor='black', facecolor=facecolor, alpha=0.5)
        return polygon
    def draw_orientation(self, scale=None):
        # Draw the orientation of the rectangle
        if scale is None:
            scale = (self.width+self.height) * 0.8
        orientation = self.parent_frame @ self.transformation
        orientation.draw_orientation(scale=scale)
    def draw_end_orientation(self, scale=None):
        # Draw the end orientation of the rectangle
        if scale is None:
            scale = (self.width+self.height) * 0.8
        self.next_frame.draw_orientation(scale=scale)
