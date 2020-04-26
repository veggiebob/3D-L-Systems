from typing import List

from tremor.graphics.element_renderer import ElementRenderer
from tremor.math.transform import Transform


class SceneElement:
    def __init__(self, name):
        self.transform = Transform(self)
        self.renderer: ElementRenderer = None
        self.name = name
        self._node_idx = -1
        self.children: List[SceneElement] = []
        self.parent: SceneElement = None

    def __str__(self):
        return self.name + " (SceneElement-" + str(self.__hash__()) + ")"

    def is_renderable(self):
        return self.renderer is not None
