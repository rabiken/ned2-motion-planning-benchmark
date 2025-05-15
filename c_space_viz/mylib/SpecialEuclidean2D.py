# visualization of c space for robotics
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


# Rotation class for 2D
class Rotation2D:
    def __init__(self, angle=0.0):
        self.angle = angle
    def set_angle(self, angle):
        self.angle = angle
    def get_angle(self):
        return self.angle
    def get_rotation_matrix(self):
        return np.array([[np.cos(self.angle), -np.sin(self.angle)],
                         [np.sin(self.angle), np.cos(self.angle)]])

# Translation class for 2D
class Translation2D:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    def set_translation(self, x, y):
        self.x = x
        self.y = y
    def get_translation_vector(self):
        return np.array([self.x, self.y])

# Special Euclidean class for 2D
class SpecialEuclidean2D():
    def __init__(self, angle=0.0, x=0.0, y=0.0):
        self.n_dimensions = 2 # This prototype is only for 2D space
        self.rotation = Rotation2D(angle=angle)  # rotation angle
        self.translation = Translation2D(x=x,y=y) # translation vector
    def set_rotation(self, angle):
        self.rotation.set_angle(angle)
    def set_translation(self, x, y):
        self.translation.set_translation(x, y)
    def get_translation(self):
        return self.translation
    def get_transformation_matrix(self):
        R = self.rotation.get_rotation_matrix()
        t = self.translation.get_translation_vector()
        T = np.eye(self.n_dimensions + 1)   # 3x3 identity matrix
        T[0:2, 0:2] = R
        T[0:2, 2] = t
        return T

    def __matmul__(self, other):
        if isinstance(other, SpecialEuclidean2D):
            T2 = other.get_transformation_matrix()
        else:
            T2 = other
        T1 = self.get_transformation_matrix()
        result = SpecialEuclidean2D()
        T_result = T1 @ T2
        result.set_rotation(np.arctan2(T_result[1, 0], T_result[0, 0]))
        result.set_translation(T_result[0, 2], T_result[1, 2])
        return result
    
    def draw_orientation(self, scale=1.0):
        # Plot the orientation of the object
        R = self.rotation.get_rotation_matrix()
        origin = self.translation.get_translation_vector()
        arrow_length = scale * 0.5
        plt.quiver(origin[0], origin[1], R[0, 0] * arrow_length, R[1, 0] * arrow_length,
                   angles='xy', scale_units='xy', scale=1, color='r')
        plt.quiver(origin[0], origin[1], R[0, 1] * arrow_length, R[1, 1] * arrow_length,
                   angles='xy', scale_units='xy', scale=1, color='g')
