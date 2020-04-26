from typing import List

from tremor.core.scene_element import SceneElement


class Scene:
    def __init__(self, name: str):
        self.name = name
        self.elements: List[SceneElement] = []
        self.active_camera: SceneElement = None

    def tick(self):
        pass
