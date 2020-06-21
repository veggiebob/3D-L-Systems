import time
from typing import List

from main import main
from main.graphics.mesh import Mesh
from main.math.transform import Transform


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
        if main.exceeded_max_render_time():
            # print('overtime at entity level!')
            return
        if self.is_renderable():
            self.mesh.render(self.transform)
        for c in self.children:
            c.render()

    def is_renderable(self):
        return self.mesh is not None
