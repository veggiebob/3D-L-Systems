import vertex_math

import OpenGL

OpenGL.USE_ACCELERATE = False
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from array import array
from vbo import *
from shaders import *
from uniforms import *
import numpy as np
import sys
from vertex_math import *
program = None
vbo, nvbo = None, None
window = None

framecount = 0

# add_uniform('mouse', 'vec2')
add_uniform('time', 'float')
inputs = {'mouse': [0, 0]}  # this is probably bad

vertex_pos = np.array(
    [0.75, 0.75, 0.0,
     0.75, -0.75, 0.0,
     -0.75, -0.75, 0.0],
    dtype='float32'
)
normals = get_normals(vertex_pos)


def create_window(size, pos, title):
    glutInitWindowSize(size[0], size[1])
    glutInitWindowPosition(pos[0], pos[1])
    return glutCreateWindow(title)


def render():
    global framecount
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(program)

    vbo.bind()
    glEnableVertexAttribArray(0)
    update_uniform('time', [float(framecount)])
    update_uniform('mouse', inputs['mouse'])
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

    nvbo.bind()
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 0, None)

    glDrawArrays(GL_TRIANGLES, 0, 3)
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)

    glUseProgram(0)
    glutSwapBuffers()
    framecount += 1


def reshape(w, h):
    glViewport(0, 0, w, h)


def keyboard(key, x, y):
    if ord(key) == 27:
        glutLeaveMainLoop()
        return
    inputs['key'] = key


def continuous_mouse(x, y):
    inputs['mouse'] = [x, y]
    glutPostRedisplay()


def main():
    global program, window, vbo, nvbo
    glutInit(sys.argv)
    display_mode = GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH | GLUT_STENCIL
    glutInitDisplayMode(display_mode)
    window = create_window((640, 480), (0, 0), "Quake-like")
    program = create_all_shaders()
    init_uniforms(program)  # create uniforms for the frag shader
    vbo = VertexBufferObject()
    vbo.update_data(vertex_pos)
    glBindVertexArray(glGenVertexArrays(1))
    nvbo = VertexBufferObject()
    nvbo.update_data(normals)
    glBindVertexArray(glGenVertexArrays(1))

    glutDisplayFunc(render)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMotionFunc(continuous_mouse)
    glutPassiveMotionFunc(continuous_mouse)
    glutMainLoop()


if __name__ == "__main__":
    main()
