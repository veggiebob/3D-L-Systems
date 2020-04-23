from typing import List, Dict

import pygltflib
from scipy.spatial.transform import Rotation as R

import PIL
import numpy as np
import OpenGL
import OpenGL.GL as GL
from PIL import Image

import matrix
import texture_loading
import vertex_math
from uniforms import update_uniform, Texture

"""
todo steps:
    initialization:
     - create a vao
     - create/update vbos
        - bind vao
        - generate vbo
        - bind vbo
        - add data to vbo
        - unbind vbo*
        - unbind vao
    rendering:
     - bind vao
     - enable vao
     - draw it
     - disable vao
     - unbind it
"""
class Attribute:
    def __init__(self, location=0, name="none", vbo_id=0, size:int=3):
        self.name = name
        self.location = location
        self.vbo_id = vbo_id
        self.size = size
class Attributes:
    def __init__(self):
        self.attributes:List[Attribute] = []
    def name_in_attributes (self, name:str) -> bool:
        for a in self.attributes:
            if a.name == name:
                return True
        return False
    def location_in_attributes (self, location) -> bool:
        for a in self.attributes:
            if a.location == location:
                return True
        return False
    def vbo_id_in_attributes (self, vbo_id:int):
        for a in self.attributes:
            if a.vbo_id == vbo_id:
                return True
        return False
    def add_attribute(self, name:str, location, vbo_id:int, size:int):
        if not self.name_in_attributes(name) and not self.location_in_attributes(location) and not self.vbo_id_in_attributes(vbo_id):
            self.attributes.append(Attribute(name=name, location=location, vbo_id=vbo_id, size=size))

class RenderableObject:
    UP = np.array([0, 1, 0], dtype='float32')
    def __init__(self):
        self.vaoID = GL.glGenVertexArrays(1)
        self.attributes = Attributes()
        self.vertex_count = 0
        self.face_count = 0

        # uniforms
        self.material = Material()

        # initials
        self.initial_translation = np.array([0, 0, 0], dtype='float32')
        self.initial_quaternion = np.array([0, 0, 0, 1], dtype='float32')

        # realtime
        self.translation = np.array([0, 0, 0], dtype='float32')
        self.scale:np.array = np.array([1, 1, 1])

        self.euler_rot = np.array([0, 0, 0], dtype='float32')
        self.quaternion = np.array([0, 0, 0, 1], dtype='float32')
        self.using_quaternions = True

        self.has_uvs = False

    def set_material (self, material:'Material') -> None:
        self.material = material

    def set_image (self, image:Image):
        # self.image_data = np.asarray(image, dtype='float32').flatten()
        # self.image_size = image.size
        data = np.asarray(image, dtype='float32').flatten()
        mode = image.mode.lower()
        form = GL.GL_RGBA if mode=='rgba' else (GL.GL_RGB if mode=='rgb' else print('unknown format %s'%mode)) # default is RGB
        tex = Texture(data, name='unnamed', width=image.width(), height=image.height(), img_format=form)
        self.set_texture(tex)

    def set_texture (self, tex:Texture):
        self.material.set_texture(tex, MaterialTexture.COLOR)

    def bind_float_attribute_vbo (self, data, attribute_name:str, static: bool, program, size:int=3): # must be 4 byte floats
        # print('received data %s' % data)
        # todo: should add support for index vs. attribute_name
        self.bind_vao()
        if attribute_name=='position':
            self.vertex_count = int(len(data) / 3)
        vbo_id = GL.glGenBuffers(1)
        location = GL.glGetAttribLocation(program, attribute_name)
        # print('location is %s for %s'%(location, attribute_name))
        self.attributes.add_attribute(name=attribute_name, location=location, vbo_id=vbo_id, size=size)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_id) # bind it
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW if static else GL.GL_DYNAMIC_DRAW) # add the data into it
        GL.glVertexAttribPointer(location, size, GL.GL_FLOAT, GL.GL_FALSE, 0, None) # tell it how to parse it
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0) # unbind it
        self.unbind_vao()

    def get_translation_matrix (self):
        trans_mat = matrix.create_translation_matrix(self.translation + self.initial_translation)
        # print('trans_mat: \n%s'%trans_mat)
        return trans_mat

    def get_euler_matrix (self):
        heading = vertex_math.euler(self.euler_rot[0], self.euler_rot[1], self.euler_rot[2], np.array([1, 0, 0], dtype='float32'))
        norm = vertex_math.euler(self.euler_rot[0], self.euler_rot[1], self.euler_rot[2], np.array([0, 1, 0], dtype='float32'))
        T = vertex_math.norm_vec3(heading)
        N = norm
        B = np.cross(N, T)
        rot_mat = matrix.create_rotation_matrix(T, N, B)
        return rot_mat

    def set_quat (self, forward, angle_rad):
        self.quaternion = np.append(
                np.asarray(forward) * np.sin(angle_rad),
                np.cos(angle_rad)
            )

    def get_quat_matrix (self):
        rot = np.zeros((4, 4), dtype='float32')
        quat = vertex_math.quaternion_multiply(self.initial_quaternion, self.quaternion)
        # quat = self.quaternion
        rot[:3,:3] = R.from_quat(quat).as_matrix()
        rot[3,3] = 1 # be a good bean
        return rot

    def get_scale_matrix (self):
        return matrix.create_scale_matrix(*self.scale)

    def get_model_view_matrix (self):
        rot = self.get_quat_matrix() if self.using_quaternions else self.get_euler_matrix()
        return self.get_scale_matrix().dot( # scale it
                    rot.dot( # rotate it
                        self.get_translation_matrix())) # translate it

    def render (self):
        # https://github.com/TheThinMatrix/OpenGL-Tutorial-3/blob/master/src/renderEngine/Renderer.java #render
        update_uniform('modelViewMatrix', [1, GL.GL_FALSE, self.get_model_view_matrix().transpose()])
        update_uniform('isTextured', [self.has_uvs])
        if self.material.has_texture(MaterialTexture.COLOR):
            texture_loading.get_texture('texColor').transfer(self.material.get_texture(MaterialTexture.COLOR)) # todo: bad
        self.bind_vao()
        for a in self.attributes.attributes:
            GL.glEnableVertexAttribArray(a.location)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, a.vbo_id)
            GL.glVertexAttribPointer(a.location, a.size, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count)
        for a in self.attributes.attributes:
            GL.glDisableVertexAttribArray(a.location)
        self.unbind_vao()

    def bind_vao (self):
        GL.glBindVertexArray(self.vaoID)

    def unbind_vao (self):
        GL.glBindVertexArray(0)

class Material:
    LightingModels:Dict[str, Dict[str, type]] = { # currently unused, but might be helpful for shaders or something
        'PHONG': {
            'diffuse': float,
            'specular': float,
            'ambient': float,
            'shinyness': float
        }
    }
    @staticmethod
    def from_gltf_material (gltf_mat:pygltflib.Material, color_texture:Texture=None, metallic_texture:Texture=None, normal_texture:Texture=None) -> 'Material':
        mat = Material(gltf_mat.name)
        if color_texture is not None:
            mat.set_texture(color_texture, MaterialTexture.COLOR)
        if metallic_texture is not None:
            mat.set_texture(metallic_texture, MaterialTexture.METALLIC)
        if normal_texture is not None:
            mat.set_texture(normal_texture, MaterialTexture.NORMAL)

        pbr = gltf_mat.pbrMetallicRoughness
        mat.base_color = pbr.baseColorFactor
        mat.metallic_factor = pbr.metallicFactor
        mat.roughness_factor = pbr.roughnessFactor
        mat.emissive_factor = gltf_mat.emissiveFactor
        return mat

    def __init__ (self, name:str='unnamed', **kwargs):
        self.name = name

        # the textures
        self.textures:Dict[int, MaterialTexture] = {
            MaterialTexture.COLOR: MaterialTexture(MaterialTexture.COLOR),
            MaterialTexture.METALLIC: MaterialTexture(MaterialTexture.METALLIC),
            MaterialTexture.NORMAL: MaterialTexture(MaterialTexture.NORMAL)
        }

        self.base_color:np.array = np.array([1, 1, 1])
        self.metallic_factor:float = 1.0 # [0, 1]
        self.roughness_factor:float = 1.0 # [0, 1]
        self.emissive_factor:np.array = np.array([0.0, 0.0, 0.0])
        for k, v in kwargs.items():
            if not hasattr(self, k):
                print('not sure what %s is, but setting it to material %s anyway'%(k, name))
            setattr(self, k, v)

    def set_mat_texture (self, mat_texture:'MaterialTexture') -> None:
        self.textures[mat_texture.tex_type] = mat_texture

    def set_texture (self, texture:Texture, tex_type:int) -> None: # helper for set_mat_texture. they do the same thing
        self.set_mat_texture(MaterialTexture(tex_type, texture))

    def get_mat_texture (self, mat_texture_type:int=None) -> 'MaterialTexture':
        if mat_texture_type is None:
            mat_texture_type = MaterialTexture.COLOR
        mat_tex = self.textures[mat_texture_type]
        if mat_tex.exists:
            return mat_tex
        else:
            raise Exception(f'material texture {mat_texture_type} does not exist')

    def get_texture (self, mat_texture_type:int=None) -> Texture:
        if mat_texture_type is None:
            mat_texture_type = MaterialTexture.COLOR
        return self.get_mat_texture(mat_texture_type).texture

    def has_texture (self, mat_texture_type:int) -> bool:
        return self.textures[mat_texture_type].exists

class MaterialTexture:
    COLOR = 0
    METALLIC = 1
    NORMAL = 2
    def __init__ (self, tex_type:int, texture:Texture=None):
        self.exists:bool = texture is not None
        self.tex_type:int = tex_type
        self.texture:Texture = texture

class Transform:
    def __init__ (self):
        pass