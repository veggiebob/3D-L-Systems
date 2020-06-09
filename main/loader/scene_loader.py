from enum import Enum, unique
from io import TextIOBase
from typing import Dict, Callable

from main.core.scene import Scene
from main.loader import gltf_loader
from main.loader.scene import version0

version_map: Dict[int, Callable[[str, TextIOBase], Scene]] = {
    0: version0.load_scene0
}

def load_scene(data_stream) -> Scene:
    # read header
    format_version = int(data_stream.readline())
    try:
        loader = version_map[format_version]
    except:
        raise Exception("Unknown format version " + str(format_version))
    name = str.rstrip(data_stream.readline())
    print("Loading scene: " + name)
    return loader(name, data_stream)