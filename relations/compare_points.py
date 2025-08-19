import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict

class Location_Offsets(object):
    
    def __init__(self, camera_pos, obj_positions, obj_labels, camera_rotation=None, camera_angle=None):
        self.camera_pos = camera_pos
        self.obj_positions = obj_positions
        self.obj_labels = obj_labels
        self.camera_rotation = camera_rotation or [0.0, 0.0, 0.0]
        self.camera_angle = camera_angle or 0.8575560450553894  # ~49 degrees
        self.offset_data = self.compare_all_points()
        # self.show_data_range()
        
    def get_obj_offsets(self, idx):
        offsets_by_obj = {}
        for x, y in self.offset_data:
            if x == idx:
                offsets_by_obj[y] = self.offset_data[(x,y)]
        return offsets_by_obj

    def compare_all_points(self):
        
        # offset_data = {}
        location_offsets = {}
        self.max_distance_x = 0
        self.min_distance_x = 1000
        self.max_distance_y = 0
        self.min_distance_y = 1000
        self.max_degrees = 0
        self.min_degrees = 1000
        self.max_radians = 0
        self.min_radians = 1000
        self.max_cos_theta = 0
        self.min_cos_theta = 1000
        self.max_sin_theta = 0
        self.min_sin_theta = 1000
        
        
        for i in range(len(self.obj_positions)):
            for j in range(len(self.obj_positions)):
                if i != j:
                    location_offsets[(i,j)] = self.compare_points(self.obj_positions[i], self.obj_positions[j])
        
        return location_offsets

    def compare_points(self, o1_pos, o2_pos):

        # Define the positions of the camera and two objects
        camera_position = np.array(self.camera_pos)
        object1_position = np.array(o1_pos)
        object2_position = np.array(o2_pos)

        # Calculate the direction vectors from the camera to the objects
        V1 = object1_position - camera_position
        V2 = object2_position - camera_position

        # Calculate the dot product of the direction vectors
        dot_product = np.dot(V1, V2)

        # Calculate the magnitudes of the direction vectors
        magnitude_V1 = np.linalg.norm(V1)
        magnitude_V2 = np.linalg.norm(V2)

        # Calculate the cosine of the angle between the vectors
        cos_theta = dot_product / (magnitude_V1 * magnitude_V2)

        # Calculate the angle in radians
        theta_radians = np.arccos(cos_theta)

        # Convert the angle to degrees 
        theta_degrees = np.degrees(theta_radians)

        # Calculate the sine component
        sin_theta = np.sin(theta_radians)
        sin_sign = np.sign(np.cross(V1, V2))
        # print(sin_sign)
        # cos_theta = np.cos(theta_radians)

        distance = object2_position - object1_position
        direction = np.sign(distance)
        
        xyz_offsets = []
        for coord in range(len(object1_position)):
            xyz_offsets.append(object1_position[coord] - object2_position[coord])

        self.max_distance_x = max(self.max_distance_x, xyz_offsets[0])
        
        if xyz_offsets[0] > 0:
            self.min_distance_x = min(self.min_distance_x, xyz_offsets[0])

        self.max_distance_y = max(self.max_distance_y, xyz_offsets[1])
        if xyz_offsets[1] > 0:
            self.min_distance_y = min(self.min_distance_y, xyz_offsets[1])

        self.min_degrees = min(self.min_degrees, theta_degrees)
        self.max_degrees = max(self.max_degrees, theta_degrees)

        self.min_radians = min(self.min_radians, theta_radians)
        self.max_radians = max(self.max_radians, theta_radians)

        self.min_cos_theta = min(self.min_cos_theta, cos_theta)
        self.max_cos_theta = max(self.max_cos_theta, cos_theta)

        self.min_sin_theta = min(self.min_sin_theta, sin_theta)
        self.max_sin_theta = max(self.max_sin_theta, sin_theta)

        
        offsets = {'distance': distance, 'direction': direction,'xyz_offsets': xyz_offsets, 'theta_degrees': theta_degrees, 
                   'theta_radians': theta_radians, 'cos_theta':cos_theta, 'sin_theta': sin_theta }
        # print(offsets)
        return offsets
    
    def show_data_range(self):
        
        print("Max X Offset: " + str(self.max_distance_x))
        print("Min X Offset: " + str(self.min_distance_x))
        print("Max Y Offset: " + str(self.max_distance_y))
        print("Min Y Offset: " + str(self.min_distance_y))
        print("Max Degrees: " + str(self.max_degrees))
        print("Min Degrees: " + str(self.min_degrees))
        print("Max Radians: " + str(self.max_radians))
        print("Min Radians: " + str(self.min_radians))
        print("Max Cos(Theta): " + str(self.max_cos_theta))
        print("Min Cos(Theta): " + str(self.min_cos_theta))
        print("Max Sin(Theta): " + str(self.max_sin_theta))
        print("Min Sin(Theta): " + str(self.min_sin_theta))

# class Offset_Data(object):
    
#     def __init__(self, offset_data):
#         self.offset_data = offset_data
#         self.distance = self.offset_data['distance']
#         self.xyz_offsets = self.offset_data['xyz_offsets']
#         self.theta_degrees = self.offset_data['theta_degrees']
#         self.theta_radians = self.offset_data['theta_radians']
#         self.cos_theta = self.offset_data['cos_theta']
#         self.sin_theta = self.offset_data['sin_theta']
#         self.x_diff = self.xyz_offsets[0]
#         self.y_diff = self.xyz_offsets[1]
#         self.z_diff = self.xyz_offsets[2]
#         self.direction = self.offset_data['direction']
        
#     def __str__(self):
#         return "Distance: " + str(self.distance) + "\n" + \
#                "Direction: " + str(self.direction) + "\n" + \
#                "X Offset: " + str(self.x_diff) + "\n" + \
#                "Y Offset: " + str(self.y_diff) + "\n" + \
#                "Z Offset: " + str(self.z_diff) + "\n" + \
#                "Theta (Degrees): " + str(self.theta_degrees) + "\n" + \
#                "Theta (Radians): " + str(self.theta_radians) + "\n" + \
#                "Cos(Theta): " + str(self.cos_theta) + "\n" + \
#                "Sin(Theta): " + str(self.sin_theta) + "\n"

def main():
    
    # these are obtained froma blender scene
    camera_pos = [7.21, -6.83, 5.12]
    o1_pos = [-2.93, -1.75, 0.7]
    o2_pos = [0.441, 2.99, 0.7]
    o3_pos = [-1.37, 2.08, 0.7]
    o4_pos = [1.55, 0.68, 0.35]
    o5_pos = [1.01, -1.94, 0.35]
    o6_pos = [-0.25, -2.31, 0.7]
    obj_positions = [o1_pos, o2_pos, o3_pos, o4_pos, o5_pos, o6_pos]
    obj_labels = ["cylinder1", "cube1", "cube2", "cube3", "cube4", "cylinder2"]
    
    all_offsets = Location_Offsets(camera_pos, obj_positions, obj_labels)
    all_offsets.plot_points()
    all_offsets.show_data_range()
    
if __name__ == "__main__":
    main()