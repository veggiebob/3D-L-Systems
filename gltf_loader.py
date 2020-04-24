from typing import Dict, List

import PIL
from OpenGL import GL
from PIL import *
from PIL import Image as PIL_Image
from io import BytesIO

import pygltflib

import obj_loader
import texture_loading
from game_object import RenderableObject, Material
import numpy as np

from obj_loader import DummyBuffers
from uniforms import Texture

GLTF = pygltflib.GLTF2()


def glb_object(filepath) -> pygltflib.GLTF2:
    f = None
    try:
        f = open(filepath)
    except FileNotFoundError:
        raise Exception('The specified file ' + filepath + ' could not be found')
    return GLTF.load_binary(filepath)


def load_scene(filepath, program) -> List[RenderableObject]:
    obj = glb_object(filepath)
    buffer = bytearray(obj._glb_data)
    buffer_views = []
    accessors = []
    textures:List[Texture] = []
    materials:List[Material] = []
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

    for t in obj.textures:
        if t.sampler is None:
            sampler = get_default_sampler()
        else:
            sampler = obj.samplers[t.sampler]
        image = obj.images[t.source]
        data = buffer_views[image.bufferView]
        textures.append(
            load_gltf_image(image, data, sampler)
        )

    for m in obj.materials:
        try:
            color = textures[m.pbrMetallicRoughness.baseColorTexture.index]
        except: color=None
        try:
           metallic = textures[m.pbrMetallicRoughness.metallicRoughnessTexture.index]
        except: metallic=None
        try:
            normal = textures[m.normalTexture.index]
        except: normal=None
        materials.append(Material.from_gltf_material(m,
                                                     color_texture=color,
                                                     metallic_texture=metallic,
                                                     normal_texture=normal))


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

                    if prim.material is not None:
                        ro.material = materials[prim.material]
                        # material = obj.materials[prim.material]
                        # pbr = material.pbrMetallicRoughness
                        # texture = textures[pbr.baseColorTexture.index]
                        # # img = obj.images[texture.source]
                        # # sampler = obj.samplers[texture.sampler]
                        # # data = buffer_views[img.bufferView]
                        # # ro.set_texture(load_gltf_image(img, data))
                        # ro.set_texture(texture)

            ro.bind_float_attribute_vbo(positions.flatten(), 'position', True, program)
            ro.bind_float_attribute_vbo(normals.flatten(), 'normal', True, program)

            ro.initial_translation = n.translation
            ro.scale = np.array([1, 1, 1], dtype='float32') * n.scale

            ro.using_quaternions = True
            ro.initial_quaternion = n.rotation

            renderables.append(ro)

    return renderables

def get_default_sampler () -> pygltflib.Sampler:
    print('created default sampler')
    sampler = pygltflib.Sampler()
    sampler.wrapS = pygltflib.CLAMP_TO_EDGE  # U # REPEAT
    sampler.wrapT = pygltflib.CLAMP_TO_EDGE  # V
    sampler.minFilter = pygltflib.NEAREST # pygltflib.LINEAR
    sampler.magFilter = pygltflib.NEAREST
    print('sampler minfilter %s'%sampler.minFilter)
    return sampler

def load_gltf_image (gltf_image:pygltflib.Image, data, sampler:pygltflib.Sampler) -> Texture:
    img = PIL_Image.open(BytesIO(data))
    # img.show()
    mode = accessor_color_type(img.mode)
    data = np.array(img.getdata(), dtype=np.uint8).flatten()
    sample_mode = accessor_sampler_type(sampler.minFilter)
    clamp_mode = accessor_sampler_type(sampler.wrapS)
    tex = Texture(data, gltf_image.name, width=img.width, height=img.height, img_format=mode, sample_mode=sample_mode, clamp_mode=clamp_mode)
    return tex

pil2gl_bands = {
    'rgba': GL.GL_RGBA,
    'rgb': GL.GL_RGB
}

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

gltf_samp_types: Dict[int, type] = {
    # mag / min filters
    9728: GL.GL_NEAREST,
    9729: GL.GL_LINEAR,
    9984: GL.GL_NEAREST_MIPMAP_NEAREST,
    9985: GL.GL_LINEAR_MIPMAP_NEAREST,
    9986: GL.GL_NEAREST_MIPMAP_LINEAR,
    9987: GL.GL_LINEAR_MIPMAP_LINEAR,
    # wrap types
    33071: GL.GL_CLAMP_TO_EDGE,
    33648: GL.GL_MIRRORED_REPEAT,
    10497: GL.GL_REPEAT
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

def accessor_color_type (typ:str):
    try:
        return pil2gl_bands[typ.lower()]
    except:
        raise Exception('HEY what is color type %s'%typ)

def accessor_sampler_type (typ: int):
    try:
        return gltf_samp_types[typ]
    except:
        raise Exception('HEY what is sampler type %d'%typ)