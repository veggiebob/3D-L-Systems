from typing import List

from tremor.core.entity import Entity


class Scene:
    def __init__(self, name: str):
        self.name = name
        self.active_camera: Entity = None
        self.entities: List[Entity] = None

    def tick(self):
        pass
