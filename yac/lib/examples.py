import os
from yac.lib.paths import get_yac_path

def get_all_keys():

    keys = []
    root_path = get_yac_path()

    for root, dirs, files in os.walk(os.path.join(root_path,"examples")):
        if "service.json" in files:
            example_paths = root[root.rfind("examples"):]
            path_elements = example_paths.split(os.sep)
            example_key = "/".join(path_elements[1:])
            keys.append(os.path.join(example_key,"service.json"))
        if "service.yaml" in files:
            example_paths = root[root.rfind("examples"):]
            path_elements = example_paths.split(os.sep)
            example_key = "/".join(path_elements[1:])
            keys.append(os.path.join(example_key,"service.yaml"))
    return keys