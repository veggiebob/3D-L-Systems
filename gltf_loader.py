from typing import Dict, List
from scipy.spatial.transform import Rotation as R

import pygltflib

import obj_loader
import texture_loading
from game_object import RenderableObject
import numpy as np

from obj_loader import DummyBuffers

GLTF = pygltflib.GLTF2()


def glb_object(filepath) -> pygltflib.GLTF2:
    f = None
    try:
        f = open(filepath)
    except FileNotFoundError:
        raise Exception('bad file stupid')
    return GLTF.load_binary(filepath)


def load_scene(filepath, program, scale=1) -> List[RenderableObject]:
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
        buffer_type = accessor_dtype(acc.componentType)
        buff = buffer_views[acc.bufferView]
        npbuff = np.frombuffer(buff, dtype=buffer_type)
        accessors.append(
            npbuff.reshape((count, vec)) # make it the right dimensions
        )

    renderables: List[RenderableObject] = []
    meshes = obj.meshes
    for n in obj.nodes:
        if n.mesh is None:
            continue
        m = meshes[n.mesh]
        # https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#reference-indices
        # goto Meshes
        for prim in m.primitives:
            attr = prim.attributes
            positions = accessors[attr.POSITION]
            normals = accessors[attr.NORMAL]  # normals are per-vertex
            ro = RenderableObject()
            ro.scale = scale
            face_index = prim.indices
            if face_index is not None:
                l = len(accessors[face_index])
                raw_faces = accessors[face_index].reshape((int(l / 3), 3))
                positions = np.asarray(obj_loader.get_vertices_from_faces(positions, raw_faces), dtype='float32')
                normals = np.asarray(obj_loader.get_vertices_from_faces(normals, raw_faces), dtype='float32')

                colors = attr.COLOR_0
                if colors is not None:
                    ro.bind_float_attribute_vbo(obj_loader.get_vertices_from_faces(accessors[colors], raw_faces).flatten(), 'color', True, program)
                texcoord = attr.TEXCOORD_0
                if texcoord is not None:
                    uvs = accessors[texcoord]
                    flat_uvs = obj_loader.get_vertices_from_faces(uvs, raw_faces).flatten()
                    ro.has_uvs = True
                    ro.bind_float_attribute_vbo(flat_uvs, 'texcoord', True, program, size=2)
                    default_tex = texture_loading.get_texture('checkers')
                    ro.set_texture(default_tex)

            ro.bind_float_attribute_vbo(positions.flatten(), 'position', True, program)
            ro.bind_float_attribute_vbo(normals.flatten(), 'normal', True, program)

            ro.translation = n.translation
            ro.scale = n.scale
            # todo: rotation? gltf gives quaternions
            # for now, use scipy
            rotation = R.from_quat(n.rotation)
            ro.euler_rot = rotation.as_euler('yxz', degrees=False)

            renderables.append(ro)

    return renderables


# https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#floating-point-data
type_to_dim: Dict[str, int] = {
    'VEC3': 3,
    'VEC2': 2,
    'SCALAR': 1
}
gltf_dtype: Dict[int, type] = {
    5120: np.int8,  # byte (1)
    5121: np.uint8,  # unsigned byte (1)
    5122: np.int16,  # short (2)
    5123: np.uint16,  # ushort (2)
    5125: np.uint32,  # uint (4)
    5126: np.float32,  # float (4)
}


def accessor_type_dim(typ: str) -> int:
    try:
        return type_to_dim[typ]
    except:
        raise Exception('HEY what is %s' % typ)


def accessor_dtype(typ: int) -> type:
    try:
        return gltf_dtype[typ]
    except:
        raise Exception('HEY what is %d' % typ)