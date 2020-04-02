import random

import OpenGL

OpenGL.USE_ACCELERATE = False
from vbo import *
from shaders import *
from uniforms import *
import sys
from vertex_math import *
from matrix import *
import test_objects
import glm
import texture_loading
import obj_loader
import camera
import pygame
from texture_loading import TEXTURES
program = None
vbo, nvbo, cvbo = None, None, None
window = None

clock = pygame.time.Clock()
framecount = 0
FPS = 120

# add_uniform('mvp', 'mat4')
add_uniform('modelViewMatrix', 'mat4')
add_uniform('projectionMatrix', 'mat4')
add_uniform('viewMatrix', 'mat4')

# add_uniform('mouse', 'vec2')
# add_uniform('time', 'float')

inputs = {'mouse': [0, 0]}  # this is probably bad



vertex_pos = np.array(
    [
    -1.0, -1.0, -1.0,
     -1.0, -1.0, 1.0,
     -1.0, 1.0, 1.0,

    -1.0, 1.0, -1.0,
     1.0, 1.0, -1.0,
     -1.0, -1.0, -1.0,

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
     1.0, -1.0, 1.0
    ],
    dtype='float32'
)
color = np.array([], dtype='float32')
normals = get_normals(vertex_pos, right_hand=False)

vertex_pos = test_objects.generate_sphere(thetaRes=80, phiRes=40)
# vertex_pos = obj_loader.load_from_file('data/models/teapot.obj')
# while len(vertex_pos)%9>0:
#     vertex_pos = vertex_pos[:-1]
color = np.array([], dtype='float32')
while len(color) < len(vertex_pos):
    color = np.append(color, np.array([random.random()], dtype='float32'))
normals = get_normals(vertex_pos)


def create_window(size, pos, title):
    glutInitWindowSize(size[0], size[1])
    glutInitWindowPosition(pos[0], pos[1])
    return glutCreateWindow(title)


def render():
    global framecount, clock
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program)
    perspective_mat = glm.perspective(glm.radians(100.0), 4.0/3.0, 0.1, 100.0)

    cam = glm.vec3(camera.spin(framecount) * 2)
    focus_point = glm.vec3([0, 0, 0])
    view_mat = glm.lookAt(cam, focus_point, glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32')

    update_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])
    # update_uniform('time', [float(framecount)])
    # update_uniform('mouse', inputs['mouse'])

    # draw normals
    # glLineWidth(3.0)
    # for tri in range(0, len(vertex_pos), 9):
    #     v1 = vertex_pos[tri:tri + 3]
    #     v2 = vertex_pos[tri + 3:tri + 6]
    #     v3 = vertex_pos[tri + 6:tri + 9]
    #     vert = (v1 + v2 + v3) / 3
    #     norm = normals[tri:tri + 3]
    #     end = vert + norm
    #     glBegin(GL_LINES)
    #     glVertex3f(vert[0], vert[1], vert[2])
    #     glVertex3f(end[0], end[1], end[2])
    #     glEnd()


    glEnableVertexAttribArray(0)
    vbo.bind()

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

    glEnableVertexAttribArray(1)
    nvbo.bind()
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 0, None)

    glEnableVertexAttribArray(2)
    cvbo.bind()
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_TRUE, 0, None)

    glDrawArrays(GL_TRIANGLES, 0, int(len(vertex_pos) / 3))
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glDisableVertexAttribArray(2)

    glUseProgram(0)
    glutSwapBuffers()
    framecount += 1
    clock.tick(FPS)
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
    display_mode = GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH | GLUT_STENCIL | GLUT_RGBA
    glutInitDisplayMode(display_mode)
    window = create_window((640, 480), (0, 0), "Quake-like")
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glDepthMask(GL_TRUE)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    program = create_all_shaders()
    init_uniforms(program)  # create uniforms for the frag shader
    texture_loading.load_all_textures('data/textures', {
        # https://open.gl/textures
        'noise_512': {
            'sample_mode': GL_LINEAR,
            'clamp_mode': GL_REPEAT
        }
    })
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
