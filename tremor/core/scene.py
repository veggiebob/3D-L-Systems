from typing import List

from tremor.core.game_object import RenderableObject
from tremor.core.scene_element import SceneElement


class Scene:
    def __init__(self, name: str):
        self.name = name
        self.elements: List[RenderableObject] = []
        self.active_camera: SceneElement = None

    def tick(self):
        pass
