import copy
import ctypes
from io import BytesIO
from typing import Dict, List, Callable

import pygltflib
from OpenGL import GL
from PIL import Image as PIL_Image

from tremor.core.entity import Entity
from tremor.graphics import shaders, fbos
from tremor.graphics.fbos import FBO
from tremor.graphics.mesh import Mesh
from tremor.graphics.surfaces import MaterialTexture, TextureUnit, Material
import numpy as np
from tremor.util import configuration

GLTF = pygltflib.GLTF2()


def glb_object(filepath) -> pygltflib.GLTF2:
    f = None
    try:
        f = open(filepath)
    except FileNotFoundError:
        raise Exception('The specified file ' + filepath + ' could not be found')
    return GLTF.load_binary(filepath)


class UnboundBuffer:
    """
    I guess here's the ones we care about:
    * GL_ARRAY_BUFFER: the most common one. For anything that uses glVertexAttribPointer
    GL_TEXTURE_BUFFER: for textures?
    GL_ELEMENT_ARRAY_BUFFER: For anything that uses glDrawElements, etc.
    GL_UNIFORM_BUFFER: probably for complicated uniforms or something

    they are all explained https://www.khronos.org/opengl/wiki/GLAPI/glBindBuffer
    """
    BIND_WITH_TARGET=True # bind immediately if there is a target

    def __init__(self, buffer_view: pygltflib.BufferView, buffer_data, index:int):
        self.buffer_view = buffer_view
        self.buffer_view_index = index
        self.data = buffer_data
        self._target = self.buffer_view.target
        self._buffer_id = None
        self.bound = False
        if UnboundBuffer.BIND_WITH_TARGET and self.has_target():
            self.bind()

    def get_buffer_id(self):
        if self._buffer_id is None:
            raise Exception('Buffer ID is null. You need to bind the buffer first.')
        return self._buffer_id

    buffer_id = property(get_buffer_id)

    def get_target(self):
        if self._target is None:
            raise Exception("Target points nowhere.")
        return self._target

    def set_target(self, new_target):
        self._target = new_target

    def has_target(self):
        return self._target is not None

    target = property(get_target, set_target)

    def bind(self, target=None, force_rebind=False) -> None:
        if self.bound and not force_rebind:
            print('buffer is already bound.')
            return
        if target is not None and not self.has_target():
            self.target = target
        if not self.has_target():
            raise Exception("Cannot bind buffer without target.")
        self._buffer_id = GL.glGenBuffers(1)
        GL.glBindBuffer(self.target, self._buffer_id)
        GL.glBufferData(target=self.target,
                        size=self.buffer_view.byteLength,
                        data=self.data,
                        usage=GL.GL_STATIC_DRAW
                        )
        GL.glBindBuffer(self.target, 0)
        self.bound = True

    # helpers
    def optional_binder (self) -> Callable:
        if not self.bound:
            return self.bind
        else:
            return lambda a:a # empty do-nothing function
    def bind_as_array_buffer(self):
        self.bind(GL.GL_ARRAY_BUFFER)

    def bind_as_element_buffer(self):
        self.bind(GL.GL_ELEMENT_ARRAY_BUFFER)

    def bind_as_texture_buffer(self):
        self.bind(GL.GL_TEXTURE_BUFFER)

    def bind_as_uniform_buffer(self):
        self.bind(GL.GL_UNIFORM_BUFFER)

class UnboundBufferCollection:
    def __init__(self):
        self._buffers:List[UnboundBuffer] = []

    def add_buffer (self, buffer:UnboundBuffer):
        self._buffers.append(buffer)

    def add_buffers (self, buffer_list:List[UnboundBuffer]):
        self._buffers += buffer_list

    def get_buffer (self, buffer_view_index:int) -> UnboundBuffer:
        self._sort()
        for b in self._buffers:
            if buffer_view_index == b.buffer_view_index:
                return b
        raise Exception("could not find buffer with index %d"%buffer_view_index)

    def __add__ (self, other):
        if type(other) == list:
            self.add_buffers(other)
        else:
            self.add_buffer(other)

    def __getitem__ (self, buffer_view_index:int):
        return self.get_buffer(buffer_view_index)

    def _sort (self):
        self._buffers.sort(key=lambda buff:buff.buffer_view_index)

def load_gltf(filepath, opt_input_flags:List[str]=()) -> List[Entity]:
    obj = glb_object(filepath)
    # if not len(obj.meshes) == 1:
    #     raise Exception("only 1 mesh")
    # if not len(obj.meshes[0].primitives) == 1:
    #     raise Exception("only 1 primitive")

    # initialize gltf stuff
    blob = np.frombuffer(obj.binary_blob(), dtype='uint8')
    obj.destroy_binary_blob()
    buffers = UnboundBufferCollection()
    for i in range(len(obj.bufferViews)):
        buffer_view = obj.bufferViews[i]
        data_slice = blob[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength]
        buffers.add_buffer(UnboundBuffer(buffer_view, data_slice, index=i))

    def get_texture(index) -> TextureUnit:
        tex = obj.textures[index]
        img = obj.images[tex.source]
        data = buffers[img.bufferView].data
        if tex.sampler is not None:
            sampler = clean_sampler(obj.samplers[tex.sampler])
        else:
            sampler = get_default_sampler()
        return load_gltf_image(img, data, sampler)

    materials = []
    for material in obj.materials:
        mat = Material.from_gltf_material(material)
        if not material.alphaMode == 'OPAQUE':
            raise Exception("Special case! Discard model, and find the nearest exit.")
        color = material.pbrMetallicRoughness.baseColorTexture
        normal = material.normalTexture
        metallic = material.pbrMetallicRoughness.metallicRoughnessTexture
        if color is not None:
            mat.set_texture(get_texture(color.index), MaterialTexture.COLOR)
        if normal is not None:
            mat.set_texture(get_texture(normal.index), MaterialTexture.NORMAL)
        if metallic is not None:
            mat.set_texture(get_texture(metallic.index), MaterialTexture.METALLIC)

        # add extras just in case
        for prop,value in material.extras.items():
            if value == 'flag':
                mat.add_flag(prop)
            else:
                mat.set_property(prop, value)
        for f in opt_input_flags:
            mat.add_flag(f)
        if mat.has_flag('reflective'):
            mat.add_fbo_texture(fbos.find_fbo_by_type(FBO.REFLECTION), GL.GL_COLOR_ATTACHMENT0)
        materials.append(mat)

    # for each primitive in each mesh . . .
    entities:List[Entity] = []
    for n in obj.nodes:
        if n.mesh is None: continue
        ent = Entity(n.name)
        # do the mesh, using only the first primitive
        mesh = Mesh()
        mesh.bind_vao()
        gltf_mesh = obj.meshes[n.mesh]
        primitive = gltf_mesh.primitives[0]
        index_acc = obj.accessors[primitive.indices] if primitive.indices is not None else None
        if index_acc is not None:
            mesh.element = True
            mesh.elementInfo = index_acc
            index_buff:UnboundBuffer = buffers[index_acc.bufferView]
            index_buff.optional_binder()(GL.GL_ELEMENT_ARRAY_BUFFER)
            mesh.elementBufID = index_buff.buffer_id

            # do materials # todo: create materials, then apply to meshes
            mesh.material = None
            materialIdx = gltf_mesh.primitives[0].material
            if materialIdx is not None:
                mesh.material = copy.deepcopy(materials[materialIdx])
                if len(mesh.material.get_all_mat_textures()) == 0 or (primitive.attributes.TEXCOORD_0 is None and primitive.attributes.TEXCOORD_1 is None):
                    if primitive.attributes.COLOR_0 is not None:
                        mesh.material.add_flag('useVertexColor')
                    mesh.find_shader('flat_shaded')
                    print('using a flat shader for material %s'%mesh.material.name)
                else:
                    mesh.find_shader('default')
                    # print('using default shader for material %s'%mesh.material.name)
            else:
                mesh.set_shader(shaders.get_default_program())
                mesh.material = mesh.program.create_material()
                print('WARNING: you used a default program!')

        # do vbos
        attrs = 'COLOR_0,JOINTS_0,NORMAL,POSITION,TANGENT,TEXCOORD_0,TEXCOORD_1,WEIGHTS_0'.split(',')
        # attrs = 'COLOR_0,NORMAL,POSITION,TEXCOORD_0'.split(',')
        unsupported = 'JOINTS_0,TANGENT,TEXCOORD_1,WEIGHTS_0'.split(',') # todo: fix this
        for att in attrs:
            val = getattr(primitive.attributes, att)
            if val is None: continue
            if att in unsupported:
                print(f'WARNING: {att} in model {gltf_mesh.name} is currently unsupported and may cause problems in rendering.')
                continue
            name = att.lower()
            acc = obj.accessors[val]
            location = GL.glGetAttribLocation(mesh.gl_program, name)
            # compiler can automatically assume that a location might not exist.
            # for example, if a mesh has a texcoord_0 defined but no textures, the shader it requested will have the
            # #defines set up so that it never actually calls on the attribute texcoord_0, so the compiler pretends it does
            # not exist. Hence, this value can be -1 even if you do define everything correctly :/
            if location == -1:
                print(f'WARNING: location of {name} returned -1')
                continue
            buff = buffers[acc.bufferView]
            byte_stride = buff.buffer_view.byteStride
            if byte_stride is None:
                vec = accessor_type_dim(acc.type)
                byte_size = np.array([1], dtype=accessor_dtype(acc.componentType)).itemsize
                byte_stride = vec * byte_size

            buff.optional_binder()(GL.GL_ARRAY_BUFFER) # if not bound already, bind with that target (that target is correct for all these attributes)
            GL.glEnableVertexAttribArray(location)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buff.buffer_id)
            GL.glVertexAttribPointer(location,
                                     type_to_dim[acc.type],
                                     acc.componentType,
                                     acc.normalized,
                                     byte_stride,
                                     ctypes.c_void_p(acc.byteOffset),
                                     )
            if name == 'position': # this is ok because gltf specifies position, see attrs
                mesh.tri_count = acc.count // 3
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        mesh.unbind_vao()

        ent.mesh = mesh
        ent.transform.set_translation(n.translation)
        ent.transform.set_rotation(n.rotation)
        ent.transform.set_scale(n.scale)
        entities.append(ent)
    return entities

def get_default_sampler() -> pygltflib.Sampler:
    # print('created default sampler')
    sampler = pygltflib.Sampler()
    sampler.wrapS = pygltflib.REPEAT  # U # CLAMP_TO_EDGE
    sampler.wrapT = pygltflib.REPEAT  # V
    sampler.minFilter = pygltflib.LINEAR_MIPMAP_LINEAR  # pygltflib.LINEAR
    sampler.magFilter = pygltflib.LINEAR # this is correct!
    return sampler

def clean_sampler (sampler:pygltflib.Sampler) -> pygltflib.Sampler:
    default = get_default_sampler()
    for p in 'wrapS,wrapT,minFilter,magFilter'.split(','):
        if getattr(sampler, p) is None:
            setattr(sampler, p, getattr(default, p))
    return sampler


def load_gltf_image(gltf_image: pygltflib.Image, data, sampler: pygltflib.Sampler) -> TextureUnit:
    img:PIL_Image.Image = PIL_Image.open(BytesIO(data))
    max_dim = configuration.get_loader_settings().getint('max_texture_dimension')
    if img.width > max_dim or img.height > max_dim:
        img = img.resize((max_dim, max_dim), resample=PIL_Image.LANCZOS) # supposedly good for downsampling
    img = img.convert('RGBA')
    mode = accessor_color_type(img.mode)

    data = np.array(img.getdata(), dtype=np.uint8).flatten()
    # min_filter = accessor_sampler_type(sampler.minFilter)
    # mag_filter = accessor_sampler_type(sampler.magFilter)
    # clamp_mode = accessor_sampler_type(sampler.wrapS)
    tex = TextureUnit.generate_texture()
    tex.bind_tex2d(data, width=img.width, height=img.height, img_format=mode, sampler=sampler)
    # tex = Texture(data, gltf_image.name, width=img.width, height=img.height, img_format=mode, min_filter=min_filter,
    #               mag_filter=mag_filter, clamp_mode=clamp_mode)
    return tex


pil2gl_bands = {
    'rgba': GL.GL_RGBA,
    'rgb': GL.GL_RGB,
    # 'p': GL.GL_RGB
}

# https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#floating-point-data
type_to_dim: Dict[str, int] = {
    'MAT4': 16,
    'VEC4': 4,
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


def accessor_color_type(typ: str):
    try:
        return pil2gl_bands[typ.lower()]
    except:
        raise Exception('HEY what is color type %s' % typ)


def accessor_sampler_type(typ: int):
    try:
        return gltf_samp_types[typ]
    except:
        raise Exception('HEY what is sampler type %d' % typ)
