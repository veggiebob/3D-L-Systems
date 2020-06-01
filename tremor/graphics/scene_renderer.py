from tremor.core.scene import Scene
import glfw
import glm
import numpy as np
from OpenGL.GL import *

from tremor.graphics import screen_utils
from tremor.graphics.uniforms import update_all_uniform
from tremor.math import matrix

framecount = 0


# needs some work for UI
def render(scene: Scene):
    global framecount
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(0)
    perspective_mat = glm.perspective(glm.radians(100.0), screen_utils.aspect_ratio(), 0.1, 100000.0)
    tmat = scene.active_camera.transform._get_translation_matrix()
    rmat = scene.active_camera.transform._get_rotation_matrix()
    a = tmat.dot(rmat.dot(matrix.create_translation_matrix([1, 0, 0])))
    cam_vec = glm.vec3(scene.active_camera.transform.get_translation()[:3])
    point_at = glm.vec3(matrix.translation_from_matrix(a)[:3])
    view_mat = glm.lookAt(cam_vec, point_at, glm.vec3([0, 1, 0]))
    model_mat = np.identity(4, dtype='float32')  # by default, no transformations applied
    update_all_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_all_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_all_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])

    update_all_uniform('time', [framecount / screen_utils.MAX_FPS])  # seconds

    light_pos = [np.sin(framecount * 0.01) * 5, np.cos(framecount * 0.01) * 5, np.cos(framecount * 0.001)]
    update_all_uniform('light_pos', light_pos)

    for element in scene.elements:
        if element.is_renderable():
            if element.name == 'LIGHT':
                element.transform.set_translation(light_pos)
        element.render()
    framecount += 1
