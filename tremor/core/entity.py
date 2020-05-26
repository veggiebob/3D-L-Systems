from typing import List

from tremor.graphics.element_renderer import ElementRenderer
from tremor.graphics.mesh import Mesh
from tremor.math.transform import Transform


class Entity:
    def __init__(self):
        self.transform = Transform(self)
        self.mesh: Mesh = None
        self._node_idx = -1
        self.children: List[Entity] = []
        self.parent: Entity = None
        self.classname = ""

    def is_renderable(self):
        return self.mesh is not None
