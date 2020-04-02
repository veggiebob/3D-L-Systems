import string

from OpenGL.GL.shaders import ShaderCompilationError
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from uniforms import *
from array import array
import numpy as np

vertex_shader_string = open('data/shaders/vertex.glsl', 'r').read()
fragment_shader_string = open('data/shaders/fragment.glsl', 'r').read()

def create_all_shaders():
    program = glCreateProgram()
    shaders = [create_shader(GL_VERTEX_SHADER, vertex_shader_string),
               create_shader(GL_FRAGMENT_SHADER, fragment_shader_string)]
    for shader in shaders:
        glAttachShader(program, shader)
    glLinkProgram(program)
    status = glGetProgramiv(program, GL_LINK_STATUS)
    if status == GL_FALSE:
        print("Linker failure: " + str(glGetProgramInfoLog(program)))
    for shader in shaders:
        glDeleteShader(shader)
    return program


def create_shader(type, source):
    shader = glCreateShader(type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if status == GL_FALSE:
        raise ShaderCompilationError("Compilation failure for %s\n%s"%(str(type), glGetShaderInfoLog(shader).decode()))
    return shader
