from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from array import array
import numpy as np


class VertexBufferObject:
    def __init__(self):
        self.handle = glGenBuffers(1)

    def bind(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.handle)

    def unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_data(self, data, static=True):
        self.bind()
        glBufferData(
            GL_ARRAY_BUFFER,
            data,
            GL_STATIC_DRAW if static else GL_DYNAMIC_DRAW
        )
        self.unbind()
