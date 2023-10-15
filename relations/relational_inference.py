from scene_objects import Scene_Objects
import json
import os

def get_clevr_relations(scene_objects: Scene_Objects) -> dict:
    """
    Get the relationships between objects in a CLEVR scene.
    """
    scene_relations = {}
    entities = scene_objects.all_entities
    num_obj = scene_objects.num_objects
    
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
        
def main():
    
    data_dir = "/home/mary/Code/spatial-reasoning/custom_clevr/output/scenes/"
    scene_file = "CLEVR_train_000000.json"
    output_dir = "/home/mary/Code/spatial-reasoning/relations/"
    
    with open(os.path.join(data_dir, scene_file)) as data:
        scene_data = json.load(data)
    
    scene_info = Scene_Objects(scene_data)
    scene_relations = get_clevr_relations(scene_info)
    print(scene_relations)
    
if __name__ == "__main__":
    main()