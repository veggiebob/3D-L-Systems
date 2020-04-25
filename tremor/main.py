import OpenGL

import glfw

from tremor.loader import gltf_loader, texture_loading
from tremor.util import glutil, configuration
from tremor.core import game_clock

OpenGL.USE_ACCELERATE = False
from tremor.graphics.shaders import *
from tremor.graphics.uniforms import *
import sys
import glm
from tremor.core.game_object import *

vbo, nvbo, cvbo = None, None, None
window = None

framecount = 0
MAX_FPS: int = None
fps_clock = game_clock.FPSController()
WIDTH: int = None
HEIGHT: int = None

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

def create_uniforms ():
    # Matricies
    add_uniform_to_all('modelViewMatrix', 'mat4')
    add_uniform_to_all('projectionMatrix', 'mat4')
    add_uniform_to_all('viewMatrix', 'mat4')

    # env
    add_uniform_to_all('time', 'float')

    # other
    add_uniform_to_all('isTextured', 'bool')

def render():
    global framecount, clock
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    perspective_mat = glm.perspective(glm.radians(100.0), WIDTH/HEIGHT, 0.1, 100.0)
    cam:glm.vec3 = glm.vec3(2, 2, 2)
        #glm.vec3(camera.spin_xz(-inputs['mouse'][0] / WIDTH * 3.14159 * 2) * 2)
    focus_point = glm.vec3([0, 0, 0])
    view_mat = glm.lookAt(cam, focus_point, glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32') # by default, no transformations applied
    update_all_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_all_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_all_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])

    update_all_uniform('time', [framecount / MAX_FPS]) # seconds

    for t in test_objs:
        # t.euler_rot[1] = framecount * np.pi / 2 / FPS # do one quater-turn per second
        t.set_quat([0, 1, 0], -inputs['mouse'][0] / WIDTH * 3.14159 * 2)
        t.scale = np.array([1,1,1]) * (inputs['mouse'][1] / HEIGHT + 0.5) * 0.05
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
    print(str(error)+" : "+description.decode(), file=sys.stderr)

def main():
    global window, vbo, nvbo, cvbo
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
        glfw.CONTEXT_VERSION_MINOR: 5,
        glfw.OPENGL_DEBUG_CONTEXT: glfw.TRUE,
        glfw.OPENGL_PROFILE: glfw.OPENGL_CORE_PROFILE
    }

    window = create_window(size=(WIDTH, HEIGHT), pos="centered", title="Quake-like", monitor=screen, hints=hints,
                           screen_size=glfw.get_monitor_physical_size(glfw.get_primary_monitor()))
    glutil.log_capabilities()
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    create_all_programs()

    # create the uniforms
    create_uniforms()
    # initialize all the uniforms for all the prpograms
    init_all_uniforms()

    texture_loading.load_all_textures('data/textures', {
        # https://open.gl/textures
        'noise_512': {
            'clamp_mode': GL_REPEAT
        }
    })

    # test_obj = obj_loader.load_renderable_object_from_file('data/models/test_pyramid.obj', get_default_program(), scale=5, color=[1, 1, 1])
    # test_obj2 = obj_loader.load_renderable_object_from_file('data/models/teapot.obj', program, scale=1/50, color=[1, 0, 0])
    # test_objs = gltf_loader.load_scene('data/gltf/test_gltf/bad_cube.glb', program=get_default_program())
    test_objs = gltf_loader.load_scene('data/gltf/test_gltf/CesiumMilkTruck.glb', program=get_default_program())
    # test_objs.append(obj_loader.load_renderable_object_from_file('data/models/teapot.obj', get_default_program(), scale=1/50))
    # test_objs[-1].translation = [0, -3, 0]

    fps_clock.start()

    glfw.set_mouse_button_callback(window, mouseclick_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, keyboard_callback)

    while not glfw.window_should_close(window):
        # todo call an update method as well
        render()
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    print("Do not run this package directly!")
