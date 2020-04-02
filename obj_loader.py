import random

import pywavefront
import numpy as np

from game_object import GameObject
from vertex_math import get_normals_from_faces


def load_wav_obj (filename) -> pywavefront.Wavefront:
    return pywavefront.Wavefront(filename, collect_faces=True)

def load_game_object_from_file(filename, program) -> GameObject:
    wav = load_wav_obj(filename)
    verts = np.asarray(wav.vertices, dtype='float32').flatten()
    faces = np.asarray(wav.mesh_list[0].faces, dtype='int32').flatten()
    normals = get_normals_from_faces(wav.parser.normals, wav.mesh_list[0].faces)
    go = GameObject()
    go.bind_indices_vbo(faces)
    go.bind_float_attribute_vbo(verts, "position", True, program)
    go.bind_float_attribute_vbo(normals, "normal", True, program)
    go.bind_float_attribute_vbo(DummyBuffers.gen_grey_color_buffer(len(verts)), "color", True, program)
    return go

class DummyBuffers:
    @staticmethod
    def gen_grey_color_buffer (length, brightness=0.5):
        d = np.array([], dtype='float32')
        for i in range(length):
            d = np.append(d, brightness)
        return np.array(d, dtype='float32')

    @staticmethod
    def gen_random_color_buffer(length):
        d = np.array([], dtype='float32')
        for i in range(length):
            d = np.append(d, random.random())
        return np.array(d, dtype='float32')