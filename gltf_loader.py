from typing import Dict, List

import pygltflib

from game_object import RenderableObject
import numpy as np

from obj_loader import DummyBuffers

GLTF = pygltflib.GLTF2()
def glb_object (filepath) -> pygltflib.GLTF2:
    f = None
    try:
        f = open(filepath)
    except FileNotFoundError:
        raise Exception('bad file stupid')
    return GLTF.load_binary(filepath)

def load_scene (filepath, program) -> List[RenderableObject]:
    obj = glb_object(filepath)
    buffer = bytearray(obj._glb_data)
    buffer_views = []
    accessors = []
    for bv in obj.bufferViews:
        start = bv.byteOffset
        end = start + bv.byteLength
        buffer_views.append(buffer[start:end])

    ai = -1
    for acc in obj.accessors:
        ai += 1
        vec = accessor_type_dim(acc.type)
        count = acc.count
        buff = buffer_views[acc.bufferView]
        accessors.append(
            np.frombuffer(buff, dtype='float32')
                #.reshape((count, vec))
        )

    renderables:List[RenderableObject] = []
    for m in obj.meshes:
        # https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#reference-indices
        # goto Meshes
        for prim in m.primitives:
            attr = prim.attributes
            positions = accessors[attr.POSITION]
            normals = accessors[attr.NORMAL] # normals are per-vertex
            ro = RenderableObject()
            ro.bind_float_attribute_vbo(positions, 'position', True, program)
            ro.bind_float_attribute_vbo(normals, 'normal', True, program)
            ro.bind_float_attribute_vbo(DummyBuffers.gen_color_buffer(len(positions), [1, 1, 1]), 'color', True, program)
            renderables.append(ro)

    return renderables




type_to_dim:Dict[str, int] = {
    'VEC3': 3,
    'VEC2': 2,
    'SCALAR': 1
}
def accessor_type_dim (typ:str) -> int:
    try:
        return type_to_dim[typ]
    except:
        raise Exception('HEY what is %s'%typ)
