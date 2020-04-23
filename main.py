import random

import OpenGL

import game_clock
import gltf_loader

OpenGL.USE_ACCELERATE = False
from vbo import *
from shaders import *
from uniforms import *
import sys
from vertex_math import *
from matrix import *
import glm
import texture_loading
import obj_loader
from texture_loading import TEXTURES
from game_object import *

program = None
vbo, nvbo, cvbo = None, None, None
window = None

framecount = 0
FPS = 120
fps_clock = game_clock.FPSController()
WIDTH = 640
HEIGHT = 480

# Matricies
add_uniform('modelViewMatrix', 'mat4')
add_uniform('projectionMatrix', 'mat4')
add_uniform('viewMatrix', 'mat4')

# env
add_uniform('time', 'float')

# other
add_uniform('isTextured', 'bool')

# textures
texture_loading.add_texture('texColor', {
    'sample_mode': GL_LINEAR,
    'clamp_mode': GL_REPEAT
})

inputs = {'mouse': [0, 0]}  # this is probably bad


# test_obj:RenderableObject = None
# test_obj2:RenderableObject = None
test_objs:List[RenderableObject] = None

def create_window(size, pos, title):
    glutInitWindowSize(size[0], size[1])
    glutInitWindowPosition(pos[0], pos[1])
    return glutCreateWindow(title)


def render():
    global framecount, clock
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program)

    perspective_mat = glm.perspective(glm.radians(100.0), WIDTH/HEIGHT, 0.1, 100.0)
    cam = glm.vec3(1., 1., 1.) * 2 # camera.spin_xz(framecount) * 2)

    focus_point = glm.vec3([0, 0, 0])
    view_mat = glm.lookAt(cam, focus_point, glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32') # by default, no transformations applied

    update_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])

    update_uniform('time', [framecount / FPS]) # seconds

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

    # test_obj.translation[1] = np.cos(framecount * 0.01)
    # test_obj.translation[2] = np.sin(framecount * 0.01)

    # test_obj.euler_rot[0] = framecount * 0.003
    # test_obj.euler_rot[1] = framecount * 0.005
    #
    # test_obj2.translation[0] = np.sin(framecount * 0.005)
    #
    # test_obj.render()
    # test_obj2.render()

    for t in test_objs:
        # t.euler_rot[1] = framecount * np.pi / 2 / FPS # do one quater-turn per second
        t.set_quat([0, 1, 0], framecount * np.pi / 32 / FPS)
        t.scale = np.array([1,1,1]) * (inputs['mouse'][0] / WIDTH + 0.5)
        t.render()

    framecount += 1
    fps_clock.capFPS(FPS)

    glUseProgram(0)
    glutSwapBuffers()
    glutPostRedisplay()


def reshape(w, h):
    global WIDTH, HEIGHT
    glViewport(0, 0, w, h)
    WIDTH = w
    HEIGHT = h


def keyboard(key, x, y):
    if ord(key) == 27:
        glutLeaveMainLoop()
        return
    inputs['key'] = key


def continuous_mouse(x, y):
    inputs['mouse'] = [x, y]


def mouseclick (a, b, c, d):
    print(fps_clock.average_fps)

def main():
    global program, window, vbo, nvbo, cvbo
    # global test_obj, test_obj2
    global test_objs
    glutInit(sys.argv)
    glutInitContextVersion(4, 6)
    glutInitContextProfile(GLUT_CORE_PROFILE)
    glutInitContextFlags(GLUT_FORWARD_COMPATIBLE)
    print("OPENGL VERSION: ", glGetIntegerv(GL_MAJOR_VERSION), ".", glGetIntegerv(GL_MINOR_VERSION), sep="")
    print("OPENGL MAX_TEXTURE_SIZE:", glGetIntegerv(GL_MAX_TEXTURE_SIZE))
    display_mode = GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH | GLUT_STENCIL | GLUT_RGBA
    glutInitDisplayMode(display_mode)
    window = create_window((WIDTH, HEIGHT), (0, 0), "Quake-like")
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_DEPTH_TEST)
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

    # test_obj = obj_loader.load_renderable_object_from_file('data/models/test_pyramid.obj', program, scale=5, color=[1, 1, 1])
    # test_obj2 = obj_loader.load_renderable_object_from_file('data/models/teapot.obj', program, scale=1/50, color=[1, 0, 0])
    test_objs = gltf_loader.load_scene('data/gltf/trisout.glb', program)
    default_tex = texture_loading.get_texture('checkers')
    texture_loading.get_texture('texColor').update_data(default_tex.data, default_tex.width, default_tex.height)

    fps_clock.start()

    glutDisplayFunc(render)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMotionFunc(continuous_mouse)
    glutMouseFunc(mouseclick)
    glutPassiveMotionFunc(continuous_mouse)
    glutMainLoop()


if __name__ == "__main__":
    main()
