from typing import List

from main.core.entity import Entity
from main.graphics.vbo import VertexBufferObject
from OpenGL.GL import *


class Scene:
    def __init__(self, name: str):
        self.name = name
        self.elements: List[Entity] = []
        self.active_camera: Entity = None

    def tick(self):
        pass

    def render(self):
        for element in self.elements:
            element.render()