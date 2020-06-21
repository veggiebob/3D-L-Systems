from typing import List, Dict, Callable, Optional
import numpy as np
from main.core.entity import Entity
from main.graphics.mesh import Mesh
from main.math.transform import Spatial

class Turtle:
    # any state that is preserved, pushed or popped during the turtle's movement should be here
    # make sure to keep the copy method updated (it's important)
    def __init__ (self):
        self.spatial:'Spatial' = Spatial()
        self.resource:int = -1
    def copy (self) -> 'Turtle':
        t = Turtle()
        t.spatial = self.spatial.copy()
        t.resource = self.resource
        return t
    def __str__ (self) -> str:
        return f"Turtle(resource={self.resource}, {self.spatial})"
class LSystemGenerator:
    """
    Use a parsed L-System to generate geometry
    """

    def __init__(self, lsystem: 'LSystem'):
        self.lsystem = lsystem
        # at render
        self.sequence = self.lsystem.axiom
        self.turtle_stack:List[Turtle] = []
        self.turtle = Turtle() # we will consider the 'forward' axis being the Y axis

        self.generate_sequence()

    def generate_system (self) -> Entity:
        # run the turtle through the list of commands
        # return all the meshes todo instanced rendering
        root = Entity('l-system-root')
        root.transform = self.turtle.spatial.config_transform(root.transform)
        meshes:List[Entity] = []
        for command in self.sequence:
            if LSystem.is_action(command):
                ent:Entity = LSystem.ACTIONS[command](self)
                if ent is not None:
                    ent.parent = root
                    ent.transform._elem = ent
                    meshes.append(ent)
                    root.children.append(ent)
            elif LSystem.is_resource(command):
                self.turtle.resource = int(command)
        return root

    def generate_sequence(self):
        print('generating sequence . . . ', end='')
        self.sequence = self.lsystem.axiom
        for i in range(self.lsystem.iterations):
            self._iterate()

        print('done: %s'%self.sequence)

    def _iterate(self):
        new_seq = ""
        for ch in self.sequence:
            new_seq += self.lsystem.get_rule(ch)
        self.sequence = new_seq

    def get_current_mesh (self) -> Mesh:
        return self.lsystem.resources[self.turtle.resource]

    def action_forward(self):
        self.turtle.spatial.translation += self.turtle.spatial.j * self.turtle.spatial.scale * self.lsystem.unit_length

    def action_backward(self):
        self.turtle.spatial.translation -= self.turtle.spatial.j * self.turtle.spatial.scale * self.lsystem.unit_length

    def action_theta_cw(self):
        self.turtle.spatial.spin_j(self.lsystem.spin_angle / 180 * np.pi)

    def action_theta_ccw(self):
        self.turtle.spatial.spin_j(-self.lsystem.spin_angle / 180 * np.pi)

    def action_pitch_up(self):
        self.turtle.spatial.spin_k(self.lsystem.pitch_angle / 180 * np.pi)
    def action_pitch_down(self):
        self.turtle.spatial.spin_k(-self.lsystem.pitch_angle / 180 * np.pi)
    def action_binormal_ccw (self):
        self.turtle.spatial.spin_i(self.lsystem.binormal_angle / 180 * np.pi)
    def action_binormal_cw(self):
        self.turtle.spatial.spin_i(-self.lsystem.binormal_angle / 180 * np.pi)
    def action_increase_size (self):
        self.turtle.spatial.scale *= self.lsystem.scale_multiplier
    def action_decrease_size (self):
        self.turtle.spatial.scale /= self.lsystem.scale_multiplier
    def action_push(self):
        self.turtle_stack.append(self.turtle.copy())

    def action_pop(self):
        self.turtle = self.turtle_stack.pop()

    def action_draw_resource(self) -> Optional[Entity]:
        if self.turtle.resource < 0:
            return
        e = Entity('l-system')
        e.transform = self.turtle.spatial.config_transform(e.transform)
        e.mesh = self.get_current_mesh()
        return e

    def action_increase_resource (self):
        self.turtle.resource = (self.turtle.resource + 1)%len(self.lsystem.resources)

    def action_decrease_resource (self):
        self.turtle.resource = (self.turtle.resource - 1)%len(self.lsystem.resources)


class LSystem:
    """
    Define rules and hold data for a specific L-System

    Symbols are turtle actions
    Letters should always be user defined
    Numbers 0-9 are commands to set the resource to draw
    """
    ACTIONS:Dict[str, Callable] = {
        '+': LSystemGenerator.action_forward,
        '-': LSystemGenerator.action_backward,
        '*': LSystemGenerator.action_theta_cw, # j (green)
        '!': LSystemGenerator.action_theta_ccw,
        '^': LSystemGenerator.action_pitch_up, # k (blue)
        '&': LSystemGenerator.action_pitch_down,
        '@': LSystemGenerator.action_binormal_ccw, # i (red)
        '$': LSystemGenerator.action_binormal_cw,
        '_': LSystemGenerator.action_decrease_size,
        '=': LSystemGenerator.action_increase_size,
        '[': LSystemGenerator.action_push,
        ']': LSystemGenerator.action_pop,
        '#': LSystemGenerator.action_draw_resource,
        '`': LSystemGenerator.action_increase_resource,
        '~': LSystemGenerator.action_decrease_resource
    }

    @staticmethod
    def is_action(ch: str):
        return ch in LSystem.ACTIONS.keys()

    @staticmethod
    def is_resource(ch: str):
        return ch in '0123456789'

    def __init__(self):
        self.resources: List[Optional[Mesh]] = [None for i in range(10)]
        self.iterations = 1

        self.unit_length = 1
        self.pitch_angle = 30
        self.spin_angle = 60
        self.binormal_angle = 5
        self.scale_multiplier = 1.1
        self.axiom = ""
        self.rules: Dict[str, str] = {}

    def get_rule(self, ch: str):
        if LSystem.is_action(ch) or LSystem.is_resource(ch):
            return ch
        if ch in self.rules.keys():
            return self.rules[ch]
        print('bad character %s' % ch)
        return ''
