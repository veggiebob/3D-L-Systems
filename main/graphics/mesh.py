import ctypes

import OpenGL.GL as GL

from main.graphics import shaders
from main.graphics.shaders import MeshProgram
from main.graphics.surfaces import Material
from main.math.transform import Transform
import numpy as np


class Mesh:
    def __init__(self):
        self.vaoID = GL.glGenVertexArrays(1)
        self.program:MeshProgram = shaders.get_default_program()
        self.gl_program = self.program.program
        self.scene_model = None
        self.material:Material = self.program.create_material()
        self.tri_count = 0
        # elemented
        self.element = False # is elemented
        self.elementBufID = 0
        self.elementInfo = None

    def bind_vao(self):
        if self.vaoID is None:
            self.vaoID = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vaoID)

    def unbind_vao(self):
        GL.glBindVertexArray(0)

    def set_shader (self, shader:MeshProgram):
        self.program = shader
        self.gl_program = self.program.program

    def find_shader (self, name:str):
        self.program = shaders.query_branched_program(name, self.material)
        self.gl_program = self.program.program

    def create_material (self, name:str=None):
        self.material = self.program.create_material(name)
    def use_program (self):
        GL.glUseProgram(self.gl_program)
    def render(self, transform: Transform):
        self.bind_vao()
        GL.glUseProgram(self.gl_program)
        self.program.update_uniform('modelViewMatrix',
                                    [1, GL.GL_FALSE, transform.to_model_view_matrix_global().transpose()])
        self.program.use_material(self.material)
        if self.element:
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.elementBufID)
            # mode,count,type,indices
            GL.glDrawElements(GL.GL_TRIANGLES,
                              self.elementInfo.count,
                              GL.GL_UNSIGNED_SHORT,
                              None
                              )
        else:
            GL.glDrawArrays(GL.GL_TRIANGLES,
                            0,
                            self.tri_count)

    @staticmethod
    def create_blank_square () -> 'Mesh':
        mesh = Mesh()
        mesh.find_shader('post_processing')
        mesh.tri_count = 6
        mesh.bind_vao()
        positions = np.array([
            0, 0, 0,  1, 1, 0,  0, 1, 0,
            0, 0, 0,  1, 0, 0,  1, 1, 0
        ], dtype='float32') * 1
        uvs = np.array([
            0, 0,  1, 1,  0, 1,
            0, 0,  1, 0,  1, 1
        ], dtype='float32')
        pos_buf = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pos_buf)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, len(positions) * 4, positions, GL.GL_STATIC_DRAW)
        position_location = GL.glGetAttribLocation(mesh.gl_program, 'position')
        GL.glEnableVertexAttribArray(position_location)
        GL.glVertexAttribPointer(position_location,
                                 3,
                                 GL.GL_FLOAT,
                                 GL.GL_FALSE,
                                 0,
                                 ctypes.c_void_p(0)
                                )

        uv_buf = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, uv_buf)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, len(uvs) * 4, uvs, GL.GL_STATIC_DRAW)
        position_location = GL.glGetAttribLocation(mesh.gl_program, 'texcoord_0')
        GL.glEnableVertexAttribArray(position_location)
        GL.glVertexAttribPointer(position_location,
                                 2,
                                 GL.GL_FLOAT,
                                 GL.GL_FALSE,
                                 0,
                                 ctypes.c_void_p(0)
                                 )
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        mesh.unbind_vao()
        return mesh

