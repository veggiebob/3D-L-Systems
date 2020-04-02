import pywavefront
import numpy as np

from game_object import GameObject

def load_wav_obj (filename) -> pywavefront.Wavefront:
    return pywavefront.Wavefront(filename, collect_faces=True)
def load_game_object_from_file(filename) -> GameObject:
    wav = load_wav_obj(filename)
    verts = np.asarray(wav.vertices).flatten()
    faces = np.asarray(wav.mesh_list[0].faces).flatten() # meshes or mesh_list ????
    go = GameObject()
    go.bind_indices_vbo(faces)
    go.bind_float_attribute_vbo(verts, 0, True)
    return go