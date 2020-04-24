import OpenGL

import glfw

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
from texture_loading import TEXTURES
from game_object import *
import configuration

program = None
vbo, nvbo, cvbo = None, None, None
window = None

framecount = 0
MAX_FPS = None
fps_clock = game_clock.FPSController()
WIDTH = None
HEIGHT = None

# Matricies
add_uniform('modelViewMatrix', 'mat4')
add_uniform('projectionMatrix', 'mat4')
add_uniform('viewMatrix', 'mat4')

# env
add_uniform('time', 'float')

# other
add_uniform('isTextured', 'bool')

inputs = {'mouse': [0, 0]}  # this is probably bad

test_objs:List[RenderableObject] = None


def create_window(size, pos, title, hints, screen_size, monitor=None, share=None, ):
    if pos == "centered":
        pos = (screen_size[0]/2, screen_size[1]/2)
    glfw.default_window_hints()
    for hint, value in hints.items():
        if hint in [glfw.COCOA_FRAME_NAME, glfw.X11_CLASS_NAME, glfw.X11_INSTANCE_NAME]:
            glfw.window_hint_string(hint, value)
        else:
            glfw.window_hint(hint, value)
    win = glfw.create_window(size[0], size[1], title, monitor, share)
    glfw.set_window_pos(win, int(pos[0]), int(pos[1]))
    glfw.make_context_current(win)
    return win


def render():
    global framecount, clock
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program)

    perspective_mat = glm.perspective(glm.radians(100.0), WIDTH / HEIGHT, 0.1, 100.0)
    cam = glm.vec3(1., 1., 1.) * 2 # camera.spin_xz(framecount) * 2)

    focus_point = glm.vec3([0, 0, 0])
    view_mat = glm.lookAt(cam, focus_point, glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32') # by default, no transformations applied

    update_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])

    update_uniform('time', [framecount / MAX_FPS]) # seconds

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
        t.set_quat([0, 1, 0], framecount * np.pi / 2 / MAX_FPS)
        t.scale = np.array([1,1,1]) * (inputs['mouse'][0] / WIDTH + 0.5)
        t.render()

    framecount += 1
    fps_clock.capFPS(MAX_FPS)

    glUseProgram(0)


def reshape(w, h):
    global WIDTH, HEIGHT
    glViewport(0, 0, w, h)
    WIDTH = w
    HEIGHT = h


def keyboard_callback(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, glfw.TRUE)
        return
    if action == glfw.RELEASE:
        return
    inputs['key'] = key


def mouse_callback(window, x, y):
    inputs['mouse'] = [x, y]


def mouseclick_callback(window, button, action, modifiers):
    print(fps_clock.average_fps)

def error_callback(error, description):
    print(error+" : "+description, file=sys.stderr)

def main():

    global program, window, vbo, nvbo, cvbo
    global test_objs
    global WIDTH, HEIGHT, MAX_FPS

    glfw.set_error_callback(error_callback)

    if not glfw.init():
        print("GLFW Initialization fail!")
        return

    graphics_settings = configuration.get_graphics_settings()

    if graphics_settings is None:
        print("bla")
        return

    WIDTH = graphics_settings.getint("width")
    HEIGHT = graphics_settings.getint("height")
    MAX_FPS = graphics_settings.getint("max_fps")

    screen = None
    if graphics_settings.getboolean("full_screen"):
        screen = glfw.get_primary_monitor()

    hints = {
        glfw.DECORATED: glfw.TRUE,
        glfw.RESIZABLE: glfw.FALSE,
        glfw.CONTEXT_VERSION_MAJOR: 4,
        glfw.CONTEXT_VERSION_MINOR: 6,
        glfw.OPENGL_DEBUG_CONTEXT: glfw.TRUE,
        glfw.OPENGL_PROFILE: glfw.OPENGL_CORE_PROFILE
    }

    window = create_window(size=(WIDTH, HEIGHT), pos="centered", title="Quake-like", monitor=screen, hints=hints,
                           screen_size=glfw.get_monitor_physical_size(glfw.get_primary_monitor()))
    print("OPENGL VERSION: ", glGetIntegerv(GL_MAJOR_VERSION), ".", glGetIntegerv(GL_MINOR_VERSION), sep="")
    print("OPENGL MAX_TEXTURE_SIZE:", glGetIntegerv(GL_MAX_TEXTURE_SIZE))
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    program = create_all_shaders()
    init_uniforms(program)  # create uniforms for the frag shader
    texture_loading.add_texture('texColor', {
        'sample_mode': GL_LINEAR,
        'clamp_mode': GL_REPEAT
    })
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

    glfw.set_mouse_button_callback(window, mouseclick_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, keyboard_callback)

    while not glfw.window_should_close(window):
        #todo call an update method as well
        render()
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
