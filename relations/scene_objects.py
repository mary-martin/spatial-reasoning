import networkx as nx
import matplotlib.pyplot as plt
from compare_points import Location_Offsets

# Define a class to represent Scene Objects

class Scene_Objects(object):
    
    def __init__(self, obj_dict):
    # Initialize the object with data from the provided dictionary
        
        # scene specfic data
        self.obj_dict = obj_dict
        self.filname = obj_dict['image_filename']
        self.img_idx = obj_dict['image_index']
        self.split = obj_dict['split']
        self.directions = obj_dict['directions']
        
        # object data
        self.objects = obj_dict['objects']
        self.num_objects = len(self.objects)
        self.relationships = obj_dict['relationships']
        self.camera_pos = [7.21, -6.83, 5.12]
        self.all_entities = self.collect_objects()
        # self.show_2d_graph()
        self.obj_offsets = self.get_object_offsets()
        self.plot_points()
        self.scene_relations = self.get_combined_relations()
    
    def collect_objects(self):
        # Create Entity objects from the provided object data
        all_objects = []
        
        for i, entity in enumerate(self.objects): 
            relations = {'front': self.relationships['front'][i], 'behind': self.relationships['behind'][i], 
                         'left': self.relationships['left'][i], 'right': self.relationships['right'][i]}
            all_objects.append(Entity(entity, relations))
        return all_objects
            
    def show_2d_graph(self, plot=True):
        # Create and display a 2D graph to visualize object relationships
        G = nx.DiGraph()
        
        for i in range(self.num_objects):
            G.add_node(str(i))
        for entity in self.all_entities:
            relations = entity.relations
            for rel_type in relations.keys():
                idxs = relations[rel_type]
                if len(idxs) > 0:
                    for idx in idxs:
                        o1_entity = str(entity.idx)
                        o2_entity = str(idx)
                        if o1_entity != o2_entity:
                            G.add_edge(o1_entity, o2_entity, label=rel_type)
        if plot:
            # Create a layout for the nodes 
            layout = nx.circular_layout(G)
            # Draw the graph
            nx.draw(G, pos=layout, with_labels=True, node_size=500, node_color='skyblue', font_size=12, font_weight='bold')
            # Draw edge labels
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos=layout, edge_labels=edge_labels, font_color='red')

            plt.show()
        
    def get_object_offsets(self):
        # Calculate object offsets and store related data
        self.all_locations = []
        self.all_labels = []
        self.all_colors = []
        self.position_dict = {}
        
        for entity in self.all_entities:
            self.all_locations.append(entity.coords)
            self.position_dict[str(entity.idx)] = entity.coords[:2]
            self.all_labels.append(entity.shape + "_" + str(entity.idx))
            self.all_colors.append(entity.color)
        
        return Location_Offsets(self.camera_pos, self.all_locations, self.all_labels)
    
    def plot_points(self):
        # Create and display a 3D plot to visualize object positions

        # Create a 3D plot
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot the camera position
        ax.scatter(self.camera_pos[0], self.camera_pos[1], self.camera_pos[2], c='r', marker='o', label='Camera')

        # Plot the object positions
        j=0
        for i, obj in enumerate(self.all_locations):
            label = self.all_labels[i]
            if j == len(self.all_colors):
                j=0
            else:
                color = self.all_colors[j]
            j+=1
            ax.scatter(obj[0], obj[1], 0, c=color, marker='s', label=label)

        # Set labels for the axes
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        # Add a legend
        ax.legend()
        plt.show()
        
    def get_combined_relations(self):
        # Calculate relationships between objects in the scene

        scene_relations = {}
        entities = self.all_entities
        num_obj = self.num_objects
        
        for i in range(num_obj):
            for j in range(num_obj):
                if i != j:
                    scene_relations[(i,j)] = []
        for entity in entities:
            idx = entity.idx
            relations = entity.relations
            for key in relations.keys():
                related_objects = relations[key]
                if len(related_objects) > 0:
                    for obj in related_objects:
                        scene_relations[(idx, obj)].append(key)

        return scene_relations

    def show_combined_graph(self, plot=True):
        # Create and display a 2d combined graph to visualize object relationships

        G = nx.DiGraph()
        
        for i in self.position_dict.keys():
            G.add_node(str(i))
            
        for pair in self.scene_relations.keys():
            if len(self.scene_relations[pair]) > 0:
                all_rel = ""
                for rel in self.scene_relations[pair]:
                    all_rel = all_rel + " " + rel
                if pair[1] > pair[0]:
                    G.add_edge(str(pair[0]), str(pair[1]), label=all_rel)
        if plot:
            # Draw the graph
            nx.draw(G, pos=self.position_dict, with_labels=True, node_size=500, node_color='skyblue', font_size=12, font_weight='bold')
            # Draw edge labels
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos=self.position_dict, edge_labels=edge_labels, font_color='red')

            plt.show()
    
    def get_offset_pair(self, o1_idx, o2_idx): 
        # Get the offset between two objects
        return self.obj_offsets.offset_data[(o1_idx, o2_idx)]

class Entity(object):
    
    def __init__(self, object_info, relations):
        self.object_info = object_info
        self.relations = relations
        self.idx = int(self.object_info['idx']) - 1
        self.rotation = self.object_info['rotation']
        self.coords = self.object_info['3d_coords']
        self.shape = self.object_info['shape']
        self.size = self.object_info['size']
        self.color = self.object_info['color']
        self.front = self.relations['front']
        self.behind = self.relations['behind']
        self.left = self.relations['left']
        self.right = self.relations['right']

        