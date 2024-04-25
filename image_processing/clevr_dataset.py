import torch
from torch.utils.data import Dataset
from torchvision import transforms
from torchvision import tv_tensors
from torchvision.transforms.v2 import functional as F
from torchvision.io import read_image
from PIL import Image
import numpy as np
import json
import glob
import os


class CustomDataset(Dataset):
    def __init__(self, image_dir, metadata_dir, mask_dir, transforms):
        self.image_paths = sorted(glob.glob(f"{image_dir}/*.png"))
        self.metadata_paths = sorted(glob.glob(f"{metadata_dir}/*.json"))
        self.mask_paths = mask_dir
        self.annotations = []
        self.generate_annotations()
        self.transforms = transforms

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        image = read_image(self.image_paths[idx])[:3]
        image = tv_tensors.Image(image)

        # Get annotations for the current image
        annotation = self.annotations[idx]
        boxes = tv_tensors.BoundingBoxes(annotation["boxes"], format="XYXY", canvas_size=F.get_size(image))
        labels = torch.tensor(annotation["labels"], dtype=torch.int64)
        image_id = annotation["image_id"]
        area = torch.tensor(annotation["area"], dtype=torch.float32)
        num_objects = len(annotation["labels"])
        iscrowd = torch.zeros((num_objects,), dtype=torch.int64)

        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": image_id,
            "area": area,
            "iscrowd": iscrowd,
        }

        # If masks are available, include them in the target
        if "masks" in annotation:
            masks = annotation['masks']
            stacked_masks = torch.stack(masks, dim=0).to(torch.uint8)
            target["masks"] = tv_tensors.Mask(stacked_masks)
            
        if self.transforms is not None:
            image, target = self.transforms(image, target)
        # print(target)
        return image, target

    def generate_annotations(self):
        annotations = []
        label_to_int = {"cube": 1, "cylinder": 2, "sphere": 3}

        for img_path in self.metadata_paths:
            with open(img_path, "r") as f:
                img_data = json.load(f)

            boxes = []
            labels = []
            areas = []
            split = img_data["split"]
            filename = img_data["image_filename"]
            index = img_data["image_index"]
            img_mask_dir = os.path.join(self.mask_paths, "image_{}".format(index))
            img_masks = sorted(glob.glob(f"{img_mask_dir}/*.png"))
            obj_masks = []
            if img_masks:
                for mask_file in img_masks:
                    # we only need the first channel, all channels are identical
                    mask = read_image(mask_file)[0]
                    mask = (mask > 0).float()
                    obj_masks.append(mask)

            obj_boxes = img_data["obj_bbox"]
            objects = img_data["objects"]
            all_objects = {}
            for obj in objects:
                all_objects[str(obj["idx"])] = obj
            objects = all_objects

            for obj_index in sorted(obj_boxes.keys()):
                x0, y0, width, height = obj_boxes[obj_index]
                box = [x0, y0, x0 + width, y0 + height]
                boxes.append(box)
                label = objects[obj_index]["shape"]
                labels.append(label_to_int[label])
                area = width * height
                areas.append(area)

            annotation = {
                "split": split,
                "image_filename": filename,
                "boxes": boxes,
                "labels": labels,
                "image_id": index,
                "area": areas,
            }
            if obj_masks:
                annotation['masks'] = obj_masks
                # print(len(obj_masks))
            annotations.append(annotation)
        self.annotations = annotations
