from main.core.scene import Scene
from main.lsystems.parser import LSystem, LSystemGenerator
import numpy as np

def create_scene (lsystem:LSystem) -> Scene:
    generator = LSystemGenerator(lsystem)
    tree = generator.generate_system()
    sc = tree.transform.get_scale()
    tree.transform.set_scale(np.array([sc[0], -sc[1], sc[2]]))
    scene = Scene('lsystempreview')
    scene.elements.append(tree)
    return scene