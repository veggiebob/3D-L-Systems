from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from uniforms import *
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
uniform vec2 mouse;
uniform float time;
void main()
{
    float lerpValue = gl_FragCoord.y / 500.0f;
    vec3 col = vec3(mouse, 0.5);
    col = mix(col, vec3(sin(time * 0.1)), lerpValue);
    outputColor = vec4(col, 1.);
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
