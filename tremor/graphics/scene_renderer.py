from tremor.core.scene import Scene
import glfw
import glm
import numpy as np
from OpenGL.GL import *

from tremor.graphics import screen_utils, fbos
from tremor.graphics.fbos import FBO
from tremor.graphics.uniforms import update_all_uniform
from tremor.math import matrix
from tremor.math.transform import Transform

framecount = 0


class FBORenderer:
    def __init__ (self, fbo:FBO, scene:Scene):
        self.fbo = fbo
        self.scene = scene
    def render_with_transform (self, transform:Transform):
        tmat = transform._get_translation_matrix()
        rmat = transform._get_rotation_matrix()
        a = tmat.dot(rmat.dot(matrix.create_translation_matrix([1, 0, 0])))
        b = tmat.dot(rmat.dot(matrix.create_translation_matrix([0, 1, 0])))
        cam_vec = glm.vec3((matrix.translation_from_matrix(transform.to_model_view_matrix()))[:3])
        point_at = glm.vec3(matrix.translation_from_matrix(a)[:3])
        up_vec = glm.normalize(glm.vec3(matrix.translation_from_matrix(b)[:3]) - cam_vec)
        view_mat = glm.lookAt(cam_vec, point_at, up_vec)
        update_all_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
        self._do_render()
    def _do_render (self):
        self.fbo.prepare_render()
        self.scene.render()
        self.fbo.return_to_screen()

def render(scene: Scene):
    global framecount
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(0)
    cam_transform = scene.active_camera.transform.clone()
    reflection_render = FBORenderer(fbos.find_fbo_by_type(FBO.REFLECTION), scene)
    reflection_render.render_with_transform(cam_transform)
    perspective_mat = glm.perspective(glm.radians(90.0), screen_utils.aspect_ratio(), 0.1, 100000.0)
    tmat = cam_transform._get_translation_matrix()
    rmat = cam_transform._get_rotation_matrix()  # fine as long as we never pitch
    a = tmat.dot(rmat.dot(matrix.create_translation_matrix([1, 0, 0])))
    b = tmat.dot(rmat.dot(matrix.create_translation_matrix([0, 1, 0])))
    cam_vec = glm.vec3((matrix.translation_from_matrix(cam_transform.to_model_view_matrix()))[:3])
    point_at = glm.vec3(matrix.translation_from_matrix(a)[:3])
    up_vec = glm.normalize(glm.vec3(matrix.translation_from_matrix(b)[:3]) - cam_vec)
    view_mat = glm.lookAt(cam_vec, point_at, up_vec)
    model_mat = np.identity(4, dtype='float32')  # by default, no transformations applied
    update_all_uniform('modelViewMatrix', [1, GL_FALSE, model_mat])
    update_all_uniform('viewMatrix', [1, GL_FALSE, np.array(view_mat)])
    update_all_uniform('projectionMatrix', [1, GL_FALSE, np.array(perspective_mat)])

    update_all_uniform('time', [framecount / screen_utils.MAX_FPS])  # seconds

    light_pos = [np.sin(framecount * 0.01) * 5, np.cos(framecount * 0.01) * 5, np.cos(framecount * 0.001)]
    update_all_uniform('light_pos', light_pos)
    scene.render()
    framecount += 1
