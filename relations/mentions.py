import json


def add_mention(objects, relations, sentence, json_file):
    new_mention = {
        "sentence": sentence,
        "mentions": {"objects": objects, "relations": relations},
    }

    with open(json_file, "r") as file:
        data = json.load(file)

    data.append(new_mention)

    with open(json_file, "w") as file:
        json.dump(data, file, indent=2)


def get_objects():
    objects = []
    while True:
        object_label = input("Enter object label (or 'done' to finish): ")
        if object_label.lower() == "done":
            break

        object_id = int(input("Enter object id: "))
        object_type = input("Enter object type: ")

        object_color = input("Enter object color (optional, press enter to skip): ")
        new_object = {"id": object_id, "label": object_label, "type": object_type}

        # Conditionally add 'color' key if provided
        if object_color:
            new_object["color"] = object_color

        objects.append(new_object)

    return objects


def get_relations():
    relations = []
    while True:
        relation_label = input("Enter relation label (or 'done' to finish): ")
        if relation_label.lower() == "done":
            break

        if relation_label.lower() == "between":
            relation_o1 = int(input("Enter object id for o1: "))
            relation_o2 = int(input("Enter object id for o2: "))
            relation_o3 = int(input("Enter object id for o3: "))
            relations.append(
                {
                    "o1": relation_o1,
                    "o2": relation_o2,
                    "o3": relation_o3,
                    "label": relation_label,
                }
            )
        else:
            relation_o1 = int(input("Enter object id for o1: "))
            relation_o2 = int(input("Enter object id for o2: "))
            relations.append(
                {"o1": relation_o1, "o2": relation_o2, "label": relation_label}
            )

    return relations


if __name__ == "__main__":
    # Input for a new sentence
    new_sentence = input("Enter a new sentence: ")

    # Input for objects
    print("Enter information for objects:")
    new_objects = get_objects()

    # Input for relations
    print("Enter information for relations:")
    new_relations = get_relations()

    # File path for the JSON file
    json_file_path = "/home/mary/Code/spatial-reasoning/relations/example_expressions.json"  # Replace with the actual file path

    # Add the new mention to the JSON file
    add_mention(new_objects, new_relations, new_sentence, json_file_path)
