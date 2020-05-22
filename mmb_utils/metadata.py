import json
import os
from elf.io import open_file


def add_segmentation_to_image_dict(folder, xml_path, table_folder=None):
    assert os.path.exists(xml_path), xml_path

    image_folder = os.path.join(folder, 'images')
    image_dict_path = os.path.join(image_folder, 'images.json')

    with open(image_dict_path) as f:
        image_dict = json.load(f)

    seg_name = os.path.splitext(os.path.split(xml_path)[1])[0]
    rel_path = os.path.relpath(xml_path, image_folder)

    entry = {
        "color": "glasbey",
        "contrastLimits": [0., 1000.],
        "storage": {
            "local": rel_path,
            "remote": rel_path.replace("local", "remote")
        },
        "type": "segmentation"
    }

    if table_folder is not None:
        entry.update({"tableFolder": os.path.relpath(table_folder, folder)})

    image_dict.update({seg_name: entry})
    with open(image_dict_path, 'w') as f:
        json.dump(image_dict, f, indent=2, sort_keys=True)


def initialize_image_dict(folder, xml_path):
    assert os.path.exists(xml_path), xml_path

    image_folder = os.path.join(folder, 'images')
    image_dict_path = os.path.join(image_folder, 'images.json')

    raw_name = os.path.splitext(os.path.split(xml_path)[1])[0]
    rel_path = os.path.relpath(xml_path, image_folder)

    image_dict = {
        raw_name: {
            "color": "white",
            "contrastLimits": [0., 255.],
            "storage": {
                "local": rel_path,
                "remote": rel_path.replace("local", "remote")
            },
            "type": "image"
        }
    }

    with open(image_dict_path, 'w') as f:
        json.dump(image_dict, f, indent=2, sort_keys=True)


def initialize_bookmarks(folder, out_path, raw_name):
    bookmark_dir = os.path.join(folder, 'misc', 'bookmarks')
    os.makedirs(bookmark_dir, exist_ok=True)
    bookmark_path = os.path.join(bookmark_dir, 'default.json')

    with open_file(out_path, 'r') as f:
        shape = f['setup0/timepoint0/s0'].shape
        center = [sh // 2 for sh in shape]

    layer = {raw_name: {"maxValue": 255, "minValue": 0}}
    bkmrk = {
        "default": {"layers": layer,
                    "position": center}
    }

    with open(bookmark_path, 'w') as f:
        json.dump(bkmrk, f)
