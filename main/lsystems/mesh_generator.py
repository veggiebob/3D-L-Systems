from main.core.entity import Entity
from main.core.scene import Scene
from main.lsystems.parser import LSystem, LSystemGenerator
import numpy as np

def create_lsystem (lsystem:LSystem) -> Entity:
    generator = LSystemGenerator(lsystem)
    generator.turtle.spatial.align_j(np.array([0.0, 1.0, 0.0]))
    tree = generator.generate_system()
    # sc = tree.transform.get_scale()
    # tree.transform.set_scale(np.array([sc[0], sc[1], sc[2]]))
    # tree.transform.set_translation(np.array([0.0, 1.0, 0.0]))
    # tree.transform.set_rotation(np.array([0.707, 0.0, 0.0, 0.707]))
    return tree