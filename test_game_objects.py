from game_object import GameObject
import numpy as np

def gen_box ():
    g = GameObject()
    g.bind_float_attribute_vbo(np.array([
        -1, -1, -1,
        -1, -1,  1,
        -1,  1, -1,
        -1,  1,  1,
         1, -1, -1,
         1, -1,  1,
         1,  1, -1,
         1,  1,  1
    ], dtype='float32'), attribute_index=0, static=True)
    g.bind_indices_vbo(np.array([

    ]))