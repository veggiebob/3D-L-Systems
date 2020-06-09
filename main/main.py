from random import random

import OpenGL

from main.core.entity import Entity
from main.core.scene import Scene
from main.graphics.mesh import Mesh
from main.math.vertex_math import norm_vec3

OpenGL.USE_ACCELERATE = False

import glfw
from main.loader import scene_loader, gltf_loader
from main.util import glutil, configuration
from main.core import game_clock, console, key_input

from main.graphics.shaders import *
from main.graphics.uniforms import *
import sys
from main.graphics import screen_utils, scene_renderer, fbos
from main.math import matrix

import imgui

from imgui.integrations.glfw import GlfwRenderer

vbo, nvbo, cvbo = None, None, None
window = None

framecount = 0
MAX_FPS: int = None
fps_clock = game_clock.FPSController()

inputs = {'mouse': [0, 0]}  # this is probably bad

current_scene: Scene = None
viewangles = np.array([0, 0], dtype='float32')

imgui_renderer: GlfwRenderer = None

def create_window(size, pos, title, hints, screen_size, monitor=None, share=None, ):
    if pos == "centered":
        pos = (screen_size[0] / 2, screen_size[1] / 2)
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


def create_uniforms():
    # Matricies
    add_uniform_to_all('modelViewMatrix', 'mat4')
    add_uniform_to_all('projectionMatrix', 'mat4')
    add_uniform_to_all('viewMatrix', 'mat4')

    # env
    add_uniform_to_all('time', 'float')

    # other
    add_uniform_to_all('hasPlane', 'bool')
    add_uniform_to_all('plane', 'vec4')
    add_uniform_to_all('light_pos', 'vec3') # todo: baD



def render():
    scene_renderer.render(current_scene)
    fps_clock.capFPS(screen_utils.MAX_FPS)


def reshape(w, h):
    glViewport(0, 0, w, h)
    screen_utils.WIDTH = w
    screen_utils.HEIGHT = h

wireframe = False

def pressed(key):
    return glfw.get_key(window, key) == glfw.PRESS

def keyboard_callback(window, key, scancode, action, mods):
    global wireframe
    imgui_renderer.keyboard_callback(window, key, scancode, action, mods)
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, glfw.TRUE)
        return
    if key in key_input.bind_map.keys():
        con_cmd = key_input.bind_map[key]
        if str.startswith(con_cmd, "+"):
            if action == glfw.PRESS:
                console.handle_input(con_cmd)
            elif action == glfw.RELEASE:
                console.handle_input(str.replace(con_cmd, "+", "-", 1))
        elif action == glfw.PRESS:
            console.handle_input(con_cmd)
    if action == glfw.RELEASE:
        return
    if console.SHOW_CONSOLE:
        if key == glfw.KEY_ENTER:
            console.ENTER_PRESSED = True
        return
    if key == glfw.KEY_F:
        if action == glfw.REPEAT:
            return
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL if wireframe else GL_LINE)
        wireframe = not wireframe
    inputs['key'] = key


def mouse_callback(window, x, y):
    imgui_renderer.mouse_callback(window, x, y)
    inputs['mouse'] = [x, y]
    y = -y * 0.05
    x = -x * 0.05
    if y > 90:
        y = 90
    if y < -90:
        y = -90
    viewangles[0] = x % 360
    viewangles[1] = y
    current_scene.active_camera.transform.set_rotation(matrix.quaternion_from_angles([0, np.pi * np.mod(x/20.0 + 90, 360)/180, 0]))


def mouseclick_callback(window, button, action, modifiers):
    print(fps_clock.average_fps)
    # pass


def error_callback(error, description):
    print(str(error) + " : " + description.decode(), file=sys.stderr)


def scroll_callback(window, x, y):
    imgui_renderer.scroll_callback(window, x, y)


def resize_callback(window, w, h):
    imgui_renderer.resize_callback(window, w, h)


def char_callback(window, char):
    imgui_renderer.char_callback(window, char)

def random_unit_sphere_vec () -> np.ndarray:
    return norm_vec3([random()*2-1, random()*2-1, random()*2-1])

def main():
    global window, vbo, nvbo, cvbo
    global current_scene, flatscreen
    global imgui_renderer

    glfw.set_error_callback(error_callback)

    imgui.create_context()
    if not glfw.init():
        print("GLFW Initialization fail!")
        return

    graphics_settings = configuration.get_graphics_settings()
    loader_settings = configuration.get_loader_settings()

    if graphics_settings is None:
        print("bla")
        return

    screen_utils.WIDTH = graphics_settings.getint("width")
    screen_utils.HEIGHT = graphics_settings.getint("height")
    screen_utils.MAX_FPS = graphics_settings.getint("max_fps")

    screen = None
    if graphics_settings.getboolean("full_screen"):
        screen = glfw.get_primary_monitor()

    hints = {
        glfw.DECORATED: glfw.TRUE,
        glfw.RESIZABLE: glfw.FALSE,
        glfw.CONTEXT_VERSION_MAJOR: 4,
        glfw.CONTEXT_VERSION_MINOR: 5,
        glfw.OPENGL_DEBUG_CONTEXT: glfw.TRUE,
        glfw.OPENGL_PROFILE: glfw.OPENGL_CORE_PROFILE,
        glfw.SAMPLES: 4,
    }

    console.load_startup("startup.rc")

    window = create_window(size=(screen_utils.WIDTH, screen_utils.HEIGHT), pos="centered", title="Quake-like",
                           monitor=screen, hints=hints,
                           screen_size=glfw.get_monitor_physical_size(glfw.get_primary_monitor()))
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    imgui_renderer = GlfwRenderer(window, attach_callbacks=False)
    glutil.log_capabilities()
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    glEnable(GL_MULTISAMPLE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    create_branched_programs()

    # create the uniforms
    create_uniforms()
    # initialize all the uniforms for all the prpograms
    init_all_uniforms()
    fbos.initialize_global_fbos()

    # texture_loading.load_all_textures('data/textures', {
    #     # https://open.gl/textures
    #     'noise_512': {
    #         'clamp_mode': GL_REPEAT
    #     }
    # })
    scene_file = open("data/scenes/reflection_test.tsf", "r", encoding="utf-8")
    current_scene = scene_loader.load_scene(scene_file)
    cam = Entity("camera")
    cam.transform.set_translation(np.array([3, 3, 3]))
    cam.transform.set_rotation(matrix.quaternion_from_angles([0, np.pi/2, 0]))
    current_scene.active_camera = cam

    fps_clock.start()

    glfw.set_mouse_button_callback(window, mouseclick_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, keyboard_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_window_size_callback(window, resize_callback)
    glfw.set_char_callback(window, char_callback)

    while not glfw.window_should_close(window):
        # todo call an update method as well
        glfw.poll_events()
        imgui_renderer.process_inputs()

        # fly control
        cam.transform.set_rotation(matrix.quat_from_viewangles(viewangles))
        speed = 0.1
        if pressed(glfw.KEY_W) or pressed(glfw.KEY_UP):
            cam.transform.translate_local(np.array([speed, 0, 0]))
        if pressed(glfw.KEY_S) or pressed(glfw.KEY_DOWN):
            cam.transform.translate_local(np.array([-speed, 0, 0]))
        if pressed(glfw.KEY_A) or pressed(glfw.KEY_LEFT):
            cam.transform.translate_local(np.array([0, 0, -speed]))
        if pressed(glfw.KEY_D) or pressed(glfw.KEY_RIGHT):
            cam.transform.translate_local(np.array([0, 0, speed]))
        if pressed(glfw.KEY_LEFT_SHIFT):
            cam.transform.translate_local(np.array([0, -speed, 0]))
        if pressed(glfw.KEY_SPACE):
            cam.transform.translate_local(np.array([0, speed, 0]))
        render()
        imgui.new_frame()
        if console.SHOW_CONSOLE:
            imgui.set_next_window_bg_alpha(0.35)
            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(screen_utils.WIDTH, 110)
            imgui.begin("ConsoleWindow", False,
                        imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_SAVED_SETTINGS)
            imgui.begin_child("ConsoleOutput", 0, -25, False)
            for text, color in console.text_buffer:
                if color is None:
                    color = (0.25, 0.75, 1)
                imgui.text_colored(text, color[0], color[1], color[2], 0.8)
            imgui.text("")
            imgui.set_scroll_y(imgui.get_scroll_max_y())
            imgui.end_child()
            enter, text = imgui.input_text("Input", "", 256, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
            if enter:
                if str.startswith(text, "/"):
                    text = str.replace(text, "/", "", 1)
                    console.handle_input(text)

            imgui.end()
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
        imgui.end_frame()
        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    print("Do not run this package directly!")
