import random

import numpy as np
import trimesh

import shaders
from game_object import RenderableObject
from shaders import MeshShader
from vertex_math import *


def load_wav_obj (filename) -> trimesh.Trimesh: # except sometimes it's trimesh.Scene ?!!
    return trimesh.load(filename)

def load_renderable_object_from_file(filename, program:MeshShader=None, scale=1.0, color=(0.5, 0.5, 0.5)) -> RenderableObject:
    if program is None:
        program = shaders.get_default_program()
    # obtain relevant information from the loaded object
    obj = load_wav_obj(filename)
    raw_verts = np.asarray(obj.vertices) # 2d array
    raw_faces = np.asarray(obj.faces) # 2d array, indices
    norm_per_vert = get_normals_from_obj(raw_verts, raw_faces)
    has_uvs:bool = hasattr(obj.visual, 'uv')
    raw_uvs = None
    if has_uvs:
        raw_uvs = np.asarray(obj.visual.uv)
        raw_image = obj.visual.material.image
    else:
        raw_image = None

    verts = np.asarray(get_vertices_from_faces(raw_verts, raw_faces), dtype='float32').flatten()
    normals = np.asarray(get_stl_normals_from_faces(norm_per_vert, raw_faces), dtype='float32').flatten()
    colors = DummyBuffers.gen_color_buffer(len(verts), color)
    if has_uvs:
        uvs = np.asarray(raw_uvs, dtype='float32').flatten()
    else:
        uvs = None

    verts *= scale
    go = RenderableObject(program)
    go.bind_float_attribute_vbo(verts, "position", True)
    go.bind_float_attribute_vbo(normals, "normal", True)
    go.bind_float_attribute_vbo(colors, "color", True)
    if has_uvs:
        go.has_uvs = True
        go.bind_float_attribute_vbo(uvs, "texcoord", True)
        if raw_image is not None:
            go.set_image(raw_image)
    else:
        go.has_uvs = False
    return go

def get_vertices_from_faces (vertices, faces): # where vertices is a 2d array, and faces are indices (2d)
    # obj -> stl
    verts = []
    for f in faces:
        for fv in f:
            verts.append(vertices[fv])
    return np.asarray(verts, dtype='float32')

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