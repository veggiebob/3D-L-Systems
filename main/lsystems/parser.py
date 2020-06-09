from typing import List, Dict, Callable
import numpy as np
from main.core.entity import Entity
from main.graphics.mesh import Mesh
from main.math.transform import Spatial


class LSystemGenerator:
    """
    Use a parsed L-System to generate geometry
    """

    def __init__(self, lsystem: 'LSystem'):
        self.lsystem = lsystem
        # at render
        self.sequence = self.lsystem.axiom
        self.transform_stack = []
        self.turtle = Spatial() # we will consider the 'forward' axis being the Y axis
        self.current_mesh: Mesh = None

        self.generate_sequence()

    def generate_mesh (self) -> List[Entity]:
        # run the turtle through the list of commands
        # return all the meshes todo instanced rendering
        meshes:List[Entity] = []
        for command in self.sequence:
            if LSystem.is_action(command):
                mesh = LSystem.ACTIONS[command](self)
                if mesh is not None:
                    meshes.append(mesh)
            elif LSystem.is_resource(command):
                self.change_resource(int(command))
        return meshes

    def generate_sequence(self):
        print('generating sequence . . . ', end='')
        self.sequence = self.lsystem.axiom
        for i in range(self.lsystem.iterations):
            self._iterate()
        print('done!')

    def _iterate(self):
        new_seq = ""
        for ch in self.sequence:
            new_seq += self.lsystem.get_rule(ch)

    def change_resource(self, index: int):
        self.current_mesh = self.lsystem.resources[index]

    def action_forward(self):
        self.turtle.translation += self.turtle.j

    def action_backward(self):
        self.turtle.translation -= self.turtle.j

    def action_theta_cw(self):
        self.turtle.spin_j(self.lsystem.spin_angle / 180 * np.pi)

    def action_theta_ccw(self):
        self.turtle.spin_j(-self.lsystem.spin_angle / 180 * np.pi)

    def action_pitch_up(self):
        self.turtle.spin_i(self.lsystem.pitch_angle / 180 * np.pi)

    def action_pitch_down(self):
        self.turtle.spin_i(-self.lsystem.pitch_angle / 180 * np.pi)

    def action_push(self):
        self.transform_stack.append(self.turtle.copy())

    def action_pop(self):
        self.turtle = self.transform_stack.pop()

    def action_draw_resource(self) -> Entity:
        if self.current_mesh is None:
            return None
        e = Entity('l-system')
        e.transform = self.turtle.get_transform()
        e.mesh = self.current_mesh
        return e


class LSystem:
    """
    Define rules and hold data for a specific L-System

    Symbols are turtle actions
    Letters should always be user defined
    Numbers 0-9 are commands to set the resource to draw
    """
    ACTIONS:Dict[str, Callable] = {
        '*': LSystemGenerator.action_forward,
        '!': LSystemGenerator.action_backward,
        '-': LSystemGenerator.action_theta_cw,
        '+': LSystemGenerator.action_theta_ccw,
        '[': LSystemGenerator.action_push,
        ']': LSystemGenerator.action_pop,
        '^': LSystemGenerator.action_pitch_up,
        '&': LSystemGenerator.action_pitch_down,
        '#': LSystemGenerator.action_draw_resource
    }

    @staticmethod
    def is_action(ch: str):
        return ch in LSystem.ACTIONS.keys()

    @staticmethod
    def is_resource(ch: str):
        return ch in '0123456789'

    def __init__(self):
        self.resources: List[Mesh] = [None for i in range(10)]
        self.iterations = 1

        self.unit_length = 1
        self.pitch_angle = 30
        self.spin_angle = 60
        self.axiom = "*"
        self.rules: Dict[str, str] = {}

    def get_rule(self, ch: str):
        if LSystem.is_action(ch) or LSystem.is_resource(ch):
            return ch
        if ch in self.rules.keys():
            return self.rules[ch]
        print('bad character %s' % ch)
        return ''
