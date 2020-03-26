import numpy as np
import vertex_math


def create_projection_matrix(fov, aspect_ratio, near_clip, far_clip):
    tan_half_fov = np.tan(0.5 * fov * (np.pi / 180.0))
    arr = np.zeros((4, 4), dtype='float32')
    arr[0][0] = 1 / (aspect_ratio * tan_half_fov)
    arr[1][1] = 1 / tan_half_fov
    arr[2][2] = (far_clip + near_clip) / (near_clip - far_clip)
    arr[2][3] = -1
    arr[3][2] = (2 * far_clip * near_clip) / (near_clip - far_clip)
    return arr


def create_translation_matrix(translation_vec):
    arr = np.identity(4, dtype='float32')
    arr[0][3] = translation_vec[0]
    arr[1][3] = translation_vec[1]
    arr[2][3] = translation_vec[2]
    return arr


def create_rotation_matrix(x, y, z):
    return np.array([[x[0], x[1], x[2], 0],
                     [y[0], y[1], y[2], 0],
                     [z[0], z[1], z[2], 0],
                     [0, 0, 0, 1]], dtype='float32')


def look_at(position, target, up):
    zaxis = norm_vec3(np.subtract(position, target))
    xaxis = norm_vec3(vertex_math.cross_array(norm_vec3(up), zaxis))
    yaxis = vertex_math.cross_array(zaxis, xaxis)  # quick maths
    translation = create_translation_matrix(position * -1)
    rotation = create_rotation_matrix(xaxis, yaxis, zaxis)
    return translation * rotation


def norm_vec3(vec):
    mag = np.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])
    return np.array([vec[0] / mag, vec[1] / mag, vec[2] / mag])