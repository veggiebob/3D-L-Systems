import copy
import time
from random import random

import OpenGL

from main.core.entity import Entity
from main.core.scene import Scene
from main.graphics.mesh import Mesh
from main.lsystems import mesh_generator, openSCAD
from main.lsystems.parser import LSystem
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
MAX_RENDER_TIME = 30#ms
RENDER_START_TIME = 0
needs_restart = False
pretty_render = False
since_restart = 0

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
    global RENDER_START_TIME, needs_restart, pretty_render, since_restart
    if needs_restart:
        RENDER_START_TIME = time.perf_counter()
        scene_renderer.render(current_scene)
        frame_time = time.perf_counter() - RENDER_START_TIME
        # if not pretty_render:
        #     print(f'render time is {frame_time*1000}ms')
        # else:
        #     print(f'PRETTY RENDER at {frame_time*1000}ms')
        needs_restart = False
        if not pretty_render:
            since_restart = 0
        if since_restart == -1:
            since_restart = -1000000000000000000
            pretty_render = False
        if pretty_render:
            # for some reason if it only re-renders once then it sometimes doesn't show, so it renders again
            since_restart = -1
            needs_restart = True
    else:
        since_restart += 1

    if since_restart > 50:
        needs_restart = True
        pretty_render = True

    fps_clock.capFPS(screen_utils.MAX_FPS)

def exceeded_max_render_time () -> bool:
    return time.perf_counter() - RENDER_START_TIME > MAX_RENDER_TIME / 1000 and not pretty_render


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
    global needs_restart
    imgui_renderer.mouse_callback(window, x, y)
    dif = abs(inputs['mouse'][0] - x) + abs(inputs['mouse'][1] - y)
    if dif > 5:
        needs_restart = True
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

def main():
    global window, vbo, nvbo, cvbo
    global current_scene, flatscreen
    global imgui_renderer
    global needs_restart

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
    # glEnable(GL_CULL_FACE) # don't cull because of leaves!
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
    # scene_file = open("data/scenes/reflection_test.tsf", "r", encoding="utf-8")
    # current_scene = scene_loader.load_scene(scene_file)


    """
    out of this project https://www.khanacademy.org/computer-programming/l-systems/5646640411344896
    try making number 3 (where showProject = 3)
    """
    """
    current resource setup:
    0: straight, flat leaf
    1: oak leaf
    2: pine needle
    3: regular branch
    4: ending branch
    """
    """
    3D L Systems conventionally use this system
    '+' turn left (!)
    '-' turn right (*)
    '&' pitch down (&)
    '^' pitch up (^)
    '\' roll left (@)
    '/' roll right ($)
    
    '!' decrease size (_)
    '`' increment resource index (`)
    """
    SHOW_DEBUG_AXES = False
    ls = LSystem()
    ls.unit_length = 1.0
    ls.pitch_angle = 22.5
    ls.spin_angle = 22.5
    ls.binormal_angle = 22.5
    ls.scale_multiplier = 1.2
    ls.iterations = 5
    ls.axiom = '[S]!!!!!S'
    ls.rules = {
        'S': '3#+[&AB]****[&AB]*****[&AB]',
        'A': '__3#[B]+[&AB]****[&AB]******&AB',
        'B': '4#+1[&&#]****[&&#]****[&&#]'
    }
    leaves = gltf_loader.load_gltf('data/gltf/lsystemassets/leaves.glb', ['maskAlpha'])
    branches = gltf_loader.load_gltf('data/gltf/lsystemassets/branches.glb')
    index = 0
    for ent in leaves + branches:
        ls.resources[index] = ent.mesh
        index += 1
    current_scene = Scene('lsystempreview')
    current_scene.elements.append(gltf_loader.load_gltf('data/gltf/env_room.glb', ['skybox', 'unlit'])[0])
    tree = mesh_generator.create_lsystem(ls)

    openSCAD.generate_OpenSCAD_script(tree, output_file='data/OpenSCAD-scripts/out.scad', detail=12)

    current_scene.elements.append(tree)

    if SHOW_DEBUG_AXES:
        axes = gltf_loader.load_gltf('data/gltf/axes.glb')
        for a in axes:
            a.transform.set_scale(a.transform.get_scale() * 0.5)
        for ent in tree.children:
            debug_axis = copy.deepcopy(axes)
            for a in debug_axis:
                a.transform.set_translation(ent.transform.get_translation())
                a.transform.set_rotation(ent.transform.get_rotation())
                a.transform.set_scale(ent.transform.get_scale())
            current_scene.elements += debug_axis
        current_scene.elements += axes
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
        speed = 0.16

        if framecount > 10:
            speed *= screen_utils.MAX_FPS / fps_clock.average_fps

        should_restart = False
        if pressed(glfw.KEY_W) or pressed(glfw.KEY_UP):
            cam.transform.translate_local(np.array([speed, 0, 0]))
            should_restart = True
        if pressed(glfw.KEY_S) or pressed(glfw.KEY_DOWN):
            cam.transform.translate_local(np.array([-speed, 0, 0]))
            should_restart = True
        if pressed(glfw.KEY_A) or pressed(glfw.KEY_LEFT):
            cam.transform.translate_local(np.array([0, 0, -speed]))
            should_restart = True
        if pressed(glfw.KEY_D) or pressed(glfw.KEY_RIGHT):
            cam.transform.translate_local(np.array([0, 0, speed]))
            should_restart = True
        if pressed(glfw.KEY_LEFT_SHIFT):
            cam.transform.translate_local(np.array([0, -speed, 0]))
            should_restart = True
        if pressed(glfw.KEY_SPACE):
            cam.transform.translate_local(np.array([0, speed, 0]))
            should_restart = True

        needs_restart |= should_restart
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
