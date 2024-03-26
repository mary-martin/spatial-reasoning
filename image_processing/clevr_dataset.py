import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import numpy as np
import json

class CustomDataset(Dataset):
    def __init__(self, image_paths, metadata_paths):
        self.image_paths = image_paths
        self.metadata_paths = metadata_paths
        self.annotations = []
        self.generate_annotations()
        self.transform = transforms.Compose([
            transforms.ToTensor()
        ])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        image = Image.open(self.image_paths[idx])
        image = self.transform(image)

        # Get annotations for the current image
        annotation = self.annotations[idx]
        boxes = torch.tensor(annotation['boxes'], dtype=torch.float32)
        labels = torch.tensor(annotation['labels'], dtype=torch.int64)
        image_id = annotation['image_id']
        area = torch.tensor(annotation['area'], dtype=torch.float32)
        iscrowd = torch.tensor(np.zeros(len(annotation['labels'])), dtype=torch.uint8)

        target = {
            'boxes': boxes,
            'labels': labels,
            'image_id': image_id,
            'area': area,
            'iscrowd': iscrowd
        }

        # If masks are available, include them in the target
        if 'masks' in annotation:
            masks = torch.tensor(annotation['masks'], dtype=torch.uint8)
            target['masks'] = masks

        return image, target

    def generate_annotations(self):
        annotations = []
        label_to_int = {'cube': 0,'cylinder': 1,'sphere': 2}
        
        for img_path in self.metadata_paths:
            with open(img_path, 'r') as f:
                img_data = json.load(f)

            boxes = []
            labels = []
            areas = []
            split = img_data['split']
            filename = img_data['image_filename']

            index = img_data['image_index']
            obj_boxes = img_data['obj_bbox']
            objects = img_data['objects']
            all_objects = {}
            for obj in objects:
                all_objects[str(obj['idx'])] = obj
            objects = all_objects
            
            for obj_index in sorted(obj_boxes.keys()):
                box = obj_boxes[obj_index]
                boxes.append(box)
                label = objects[obj_index]['shape']
                labels.append(label_to_int[label])
                area = box[2] * box[3]
                areas.append(area)
            
            annotation = {
                'split': split,
                'image_filename': filename,
                'boxes': boxes,
                'labels': labels,
                'image_id': index,
                'area': areas
            }
            annotations.append(annotation)
        self.annotations = annotations