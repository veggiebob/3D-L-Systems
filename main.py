import OpenGL

OpenGL.USE_ACCELERATE = False
from vbo import *
from shaders import *
from uniforms import *
import numpy as np
import sys
from vertex_math import *
from matrix import *
import glm
program = None
vbo, nvbo, cvbo = None, None, None
window = None

framecount = 0

# add_uniform('mouse', 'vec2')
# add_uniform('time', 'float')
add_uniform('mvp', 'mat4')
add_uniform('modelViewMatrix', 'mat4')
add_uniform('projectionMatrix', 'mat4')
add_uniform('viewMatrix', 'mat4')
inputs = {'mouse': [0, 0]}  # this is probably bad

vertex_pos = np.array(
    [-1.0, -1.0, -1.0,
     -1.0, -1.0, 1.0,
     -1.0, 1.0, 1.0,
     1.0, 1.0, -1.0,
     -1.0, -1.0, -1.0,
     -1.0, 1.0, -1.0,
     1.0, -1.0, 1.0,
     -1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0, 1.0, -1.0,
     1.0, -1.0, -1.0,
     -1.0, -1.0, -1.0,
     -1.0, -1.0, -1.0,
     -1.0, 1.0, 1.0,
     -1.0, 1.0, -1.0,
     1.0, -1.0, 1.0,
     -1.0, -1.0, 1.0,
     -1.0, -1.0, -1.0,
     -1.0, 1.0, 1.0,
     -1.0, -1.0, 1.0,
     1.0, -1.0, 1.0,
     1.0, 1.0, 1.0,
     1.0, -1.0, -1.0,
     1.0, 1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0, 1.0, 1.0,
     1.0, -1.0, 1.0,
     1.0, 1.0, 1.0,
     1.0, 1.0, -1.0,
     -1.0, 1.0, -1.0,
     1.0, 1.0, 1.0,
     -1.0, 1.0, -1.0,
     -1.0, 1.0, 1.0,
     1.0, 1.0, 1.0,
     -1.0, 1.0, 1.0,
     1.0, -1.0, 1.0],
    dtype='float32'
)
color = np.array(
    [0.583,  0.771,  0.014,
    0.609,  0.115,  0.436,
    0.327,  0.483,  0.844,
    0.822,  0.569,  0.201,
    0.435,  0.602,  0.223,
    0.310,  0.747,  0.185,
    0.597,  0.770,  0.761,
    0.559,  0.436,  0.730,
    0.359,  0.583,  0.152,
    0.483,  0.596,  0.789,
    0.559,  0.861,  0.639,
    0.195,  0.548,  0.859,
    0.014,  0.184,  0.576,
    0.771,  0.328,  0.970,
    0.406,  0.615,  0.116,
    0.676,  0.977,  0.133,
    0.971,  0.572,  0.833,
    0.140,  0.616,  0.489,
    0.997,  0.513,  0.064,
    0.945,  0.719,  0.592,
    0.543,  0.021,  0.978,
    0.279,  0.317,  0.505,
    0.167,  0.620,  0.077,
    0.347,  0.857,  0.137,
    0.055,  0.953,  0.042,
    0.714,  0.505,  0.345,
    0.783,  0.290,  0.734,
    0.722,  0.645,  0.174,
    0.302,  0.455,  0.848,
    0.225,  0.587,  0.040,
    0.517,  0.713,  0.338,
    0.053,  0.959,  0.120,
    0.393,  0.621,  0.362,
    0.673,  0.211,  0.457,
    0.820,  0.883,  0.371,
    0.982,  0.099,  0.879],
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
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # update_uniform('mvp', MVP_mat.transpose())
    glUseProgram(program)
    perspective_mat = glm.perspective(glm.radians(100.0), 4.0/3.0, 0.1, 100.0)
    view_mat = glm.lookAt(glm.vec3([4, 3, 3]), glm.vec3([0, 0, 0]), glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32')

    update_uniform('modelViewMatrix', [1, GL_FALSE, np.array(model_mat)])
    update_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])
    # glUniformMatrix4fv(mvpLoc, 1, GL_TRUE, np.array(MVP_mat))

    glEnableVertexAttribArray(0)
    vbo.bind()
    # update_uniform('time', [float(framecount)])
    # update_uniform('mouse', inputs['mouse'])

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

    glEnableVertexAttribArray(1)
    nvbo.bind()
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 0, None)

    glEnableVertexAttribArray(2)
    cvbo.bind()
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_TRUE, 0, None)

    glDrawArrays(GL_TRIANGLES, 0, 3*12)
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glDisableVertexAttribArray(2)

    glUseProgram(0)
    glutSwapBuffers()
    framecount += 1
    glutPostRedisplay()


def reshape(w, h):
    glViewport(0, 0, w, h)


def keyboard(key, x, y):
    if ord(key) == 27:
        glutLeaveMainLoop()
        return
    inputs['key'] = key


def continuous_mouse(x, y):
    inputs['mouse'] = [x, y]

def main():
    global program, window, vbo, nvbo, cvbo
    glutInit(sys.argv)
    display_mode = GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH | GLUT_STENCIL
    glutInitDisplayMode(display_mode)
    window = create_window((640, 480), (0, 0), "Quake-like")
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    program = create_all_shaders()
    init_uniforms(program)  # create uniforms for the frag shader
    vbo = VertexBufferObject()
    vbo.update_data(vertex_pos)
    nvbo = VertexBufferObject()
    nvbo.update_data(normals)
    cvbo = VertexBufferObject()
    cvbo.update_data(color)
    glBindVertexArray(glGenVertexArrays(1))

    glutDisplayFunc(render)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMotionFunc(continuous_mouse)
    glutPassiveMotionFunc(continuous_mouse)
    glutMainLoop()


if __name__ == "__main__":
    main()
