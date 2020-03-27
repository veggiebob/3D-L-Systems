from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from uniforms import *
from array import array
import numpy as np

vertex_shader_string = """
#version 330
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 color;
varying vec3 fposition;
varying vec3 fnormal;
out vec3 fcolor;
uniform mat4 mvp;
void main()
{
    fposition = position;
    fnormal = normal;
    vec4 cameraPos = vec4(position, 1.0);
    gl_Position =  mvp * cameraPos;
    fcolor = color;
}
"""

fragment_shader_string = """
#version 330
out vec4 outputColor;
varying vec3 fposition;
varying vec3 fnormal;
varying vec3 fcolor;
void main()
{
    outputColor = vec4(fcolor.x, fcolor.y, fcolor.z, 1.);
}
"""

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
    status = None
    glGetShaderiv(shader, GL_COMPILE_STATUS, status)
    if status == GL_FALSE:
        print("Compilation failure for " + type + " shader:" + glGetShaderInfoLog(shader))
    return shader
