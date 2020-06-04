from typing import List

from tremor.graphics.mesh import Mesh
from tremor.math.transform import Transform


class Entity:
    def __init__(self, name:str):
        self.transform:Transform = Transform(self)
        self.mesh: Mesh = None
        self._node_idx = -1
        self.children: List[Entity] = []
        self.parent: Entity = None
        self.classname = ""
        self.name = name

    def __str__(self):
        return self.name + " (Entity-" + str(self.__hash__()) + ")"

    def render (self):
        if self.is_renderable():
            self.mesh.render(self.transform)
        for c in self.children:
            c.render()

    def is_renderable(self):
        return self.mesh is not None
