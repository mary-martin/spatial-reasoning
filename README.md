# Spatial State Estimation for Scene Understanding

### Background
In this project, we use CLEVR scene metadata, initially generated as 2D flattened blender images during the dataset creation process. To address the current lack of segmentation, we utilize the 3D locations of images extracted from JSON files containing metadata for each generated image. The `/relations` folder in the spatial-reasoning repository houses most of our project files, including:

- **relational_inference.ipynb**: A notebook for loading data and testing spatial grounding.
- **grounding.py**: Handles the grounding process.
- **mentions.py**: Expedites the human annotation task, requiring a sentence, entities, and relevant relations from the expression.
- **scene_objects.py**: Loads and stores entities from a specified CLEVR scene, automatically creating an initial 3D plot for visualization. It also stores computed offsets for objects, calculated in reference to the camera perspective.
- **compare_points.py**: Used by `scene_objects.py` to make various offset calculations between objects in the scene.

### Testing Instructions

To test the project, follow these steps:

1. In the `relational_inference` notebook, specify the directory and file name of the chosen scene data (JSON). Adjust other paths to match your system.
2. There are two testing options: create your own annotated expressions/mentions or use the provided ones.
   
   - **With Your Own Mentions:**
        - Follow the format in the `example_expressions.json` or `train_ex_01.json` files under `/relations/expressions/`.
        - Run the `mentions.py` file to automatically enter expression values into an existing JSON file or manually add to the JSON file of your choice.
   
   - **Using Our Expressions:**
        - `example_expressions.json` provides a few examples of multi-hop and combined relations for image '00000'. 
        - `train_ex_01.json` contains pairwise relations along with their 'true ranks' or expected output from a human annotator.
        
3. Following the process outlined in `relational_inference.ipynb`:
    - Load the JSON data and expressions file.
    - A 3D plot for the selected scene will be displayed if loaded correctly.
    - Create a `SpatialPredictor` object by passing the loaded scene information.
    - Use `spatial_predictor.relate()` to ground a selected mention by passing the individual mention to the object.
    - The scene is loaded and can be used repeatedly for predictions without re-initializing scene information.