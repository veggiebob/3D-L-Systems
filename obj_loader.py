import random

import pywavefront
import numpy as np
import trimesh

from game_object import RenderableObject
from vertex_math import *


def load_wav_obj (filename) -> trimesh.Trimesh:
    return trimesh.load(filename)

def load_game_object_from_file(filename, program, scale=1.0, color=(0.5, 0.5, 0.5)) -> RenderableObject:
    # todo: use trimesh
    obj = load_wav_obj(filename)
    raw_verts = np.asarray(obj.vertices) # 2d array
    raw_faces = np.asarray(obj.faces) # 2d array, indices
    norm_per_vert = get_normals_from_obj(raw_verts, raw_faces)
    verts = np.asarray(get_vertices_from_faces(raw_verts, raw_faces), dtype='float32').flatten()
    normals = np.asarray(get_stl_normals_from_faces(norm_per_vert, raw_faces), dtype='float32').flatten()
    colors = DummyBuffers.gen_color_buffer(len(verts), color)
    verts *= scale
    go = RenderableObject()
    go.bind_float_attribute_vbo(verts, "position", True, program)
    go.bind_float_attribute_vbo(normals, "normal", True, program)
    go.bind_float_attribute_vbo(colors, "color", True, program)
    return go

def get_vertices_from_faces (vertices, faces): # where vertices is a 2d array, and faces are indices (2d)
    # obj -> stl
    verts = []
    for f in faces:
        for fv in f:
            verts.append(vertices[fv])
    return verts

def get_stl_normals_from_faces (normals, faces): # normals is per-vertex 2d array, faces is 2d array indices
    # obj -> stl
    norms = []
    for f in faces:
        for fv in f:
            norms.append(normals[fv])
    return norms

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