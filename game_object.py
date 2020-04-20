from typing import List
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
        self.translation = np.array([0, 0, 0], dtype='float32')
        self.scale:np.array = np.array([1, 1, 1])

        self.euler_rot = np.array([0, 0, 0], dtype='float32')
        self.initial_quaternion = np.array([0, 0, 0, 1], dtype='float32')
        self.quaternion = np.array([0, 0, 0, 1], dtype='float32')
        self.using_quaternions = True


        self.has_uvs = False
        self.image_data = None
        self.image_size:tuple = None
    def set_image (self, image:Image):
        self.image_data = np.asarray(image, dtype='float32').flatten()
        self.image_size = image.size
    def set_texture (self, tex:Texture):
        self.image_data = np.copy(tex.data.flatten())
        self.image_size = (tex.width, tex.height)
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
        trans_mat = matrix.create_translation_matrix(self.translation)
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
        quat = self.quaternion
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
        if self.has_uvs: pass
            # texture_loading.get_texture('texColor').update_data(self.image_data, self.image_size[0], self.image_size[1]) # todo: make this not so badddd
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