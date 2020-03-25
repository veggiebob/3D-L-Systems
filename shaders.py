from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from array import array
import numpy as np

vertex_shader_string = """
#version 330
layout(location = 0) in vec4 position;
void main()
{
   gl_Position = position;
}
"""

fragment_shader_string = """
#version 330

out vec4 outputColor;

void main()
{
    float lerpValue = gl_FragCoord.y / 500.0f;
    
    outputColor = mix(vec4(1.0f, 1.0f, 1.0f, 1.0f),
        vec4(0.2f, 0.2f, 0.2f, 1.0f), lerpValue);
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
        print("Linker failure: " + glGetProgramInfoLog(program))
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
