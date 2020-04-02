import random

import pywavefront
import numpy as np

from game_object import RenderableObject
from vertex_math import *


def load_wav_obj (filename) -> pywavefront.Wavefront:
    return pywavefront.Wavefront(filename, collect_faces=True)

def load_game_object_from_file(filename, program, scale=1.0, color=(0.5, 0.5, 0.5)) -> RenderableObject:
    wav = load_wav_obj(filename)
    verts = np.asarray(wav.vertices, dtype='float32').flatten() * scale
    faces = np.asarray(wav.mesh_list[0].faces, dtype='int32').flatten()
    # normals = get_normals_from_faces(wav.parser.normals, wav.mesh_list[0].faces) # todo: fix normal loading or at least test it
    normals = np.asarray(get_normals_from_obj(wav.vertices, wav.mesh_list[0].faces)).flatten()
    go = RenderableObject()
    go.bind_indices_vbo(faces)
    go.bind_float_attribute_vbo(verts, "position", True, program)
    go.bind_float_attribute_vbo(normals, "normal", True, program)
    go.bind_float_attribute_vbo(DummyBuffers.gen_color_buffer(len(verts), color), "color", True, program)
    return go

class DummyBuffers:
    @staticmethod
    def gen_color_buffer(length, col):
        d = np.array([], dtype='float32')
        c = np.asarray(col, dtype='float32')
        for i in range(int(length/3)):
            d = np.append(d, c)
        return np.array(d, dtype='float32')
    @staticmethod
    def gen_grey_color_buffer (length, brightness=0.5):
        return DummyBuffers.gen_color_buffer(length, [brightness]*3)

    @staticmethod
    def gen_random_color_buffer(length):
        d = np.array([], dtype='float32')
        for i in range(length):
            d = np.append(d, random.random())
        return np.array(d, dtype='float32')