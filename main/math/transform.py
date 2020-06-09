import numpy as np
from scipy.spatial.transform import Rotation
from main.math import vertex_math, matrix


# A transform is a translation, rotation, and scale
class Transform:
    def __init__(self, scene_elem=None):
        self._translation = np.array([0, 0, 0], dtype='float32')  # x y z
        self._rotation = np.array([0, 0, 0, 1], dtype='float32')  # w z y x
        self._scale = np.array([1, 1, 1])  # x y z
        self._mv_needs_rebuild = True
        self._mv: np.ndarray = None
        self._elem = scene_elem

    def to_model_view_matrix(self):
        # cache mv matrix
        if self._mv_needs_rebuild:
            self._mv = self._get_translation_matrix().dot(  # apply translation
                self._get_rotation_matrix().dot(  # apply rotation
                    self._get_scale_matrix()  # apply scaling
                ))
            self._mv_needs_rebuild = False
        return self._mv

    def to_model_view_matrix_global(self):
        # non-recursive, could probably be
        mvmat = np.identity(4, dtype='float32')
        if self._has_scene_element():
            hierarchy = [self._elem]
            ce = self._elem
            while ce.parent is not None:
                hierarchy.insert(0, ce.parent)
                ce = ce.parent
            for elem in hierarchy:
                mvmat = mvmat.dot(elem.transform.to_model_view_matrix())
        return mvmat

    def _get_rotation_matrix(self):
        rot = np.zeros((4, 4), dtype='float32')

        rot[:3, :3] = Rotation.from_quat(self._rotation).as_matrix()
        rot[3, 3] = 1
        return rot

    def _get_translation_matrix(self):
        trans_mat = matrix.create_translation_matrix(self._translation)
        return trans_mat

    def _get_scale_matrix(self):
        return matrix.create_scale_matrix(*self._scale)

    def set_translation(self, trans_vec: np.ndarray):
        if not len(trans_vec) == 3:
            raise Exception("Invalid translation vector!")
        self._mv_needs_rebuild = True
        self._translation = trans_vec

    def set_rotation(self, rot_quat: np.ndarray):
        if not len(rot_quat) == 4:
            raise Exception("Invalid rotation quaternion!")
        self._mv_needs_rebuild = True
        self._rotation = rot_quat

    def set_scale(self, scale_vec: np.ndarray):
        if not len(scale_vec) == 3:
            raise Exception("Invalid scale vector!")
        self._mv_needs_rebuild = True
        self._scale = scale_vec

    def get_translation(self):
        return self._translation

    def get_rotation(self):
        return self._rotation

    def get_scale(self):
        return self._scale

    def translate_local(self, trans_vec: np.ndarray):
        if not len(trans_vec) == 3:
            raise Exception("Invalid translation vector!")
        position_mat = self._get_translation_matrix().dot(
            self._get_rotation_matrix().dot(
                matrix.create_translation_matrix(trans_vec)
            )
        )
        self.set_translation(matrix.translation_from_matrix(position_mat))

    def rotate_local(self, rot_quat: np.ndarray):
        if not len(rot_quat) == 4:
            raise Exception("Invalid rotation quaternion!")
        position_mat = self._get_translation_matrix().dot(
            self._get_rotation_matrix().dot(
                matrix.create_rotation_matrix_from_quaternion(rot_quat)
            )
        )
        self.set_rotation(matrix.quaternion_from_matrix(position_mat))

    def clone(self):
        new = Transform(self._elem)
        new._translation = self._translation.copy()
        new._scale = self._scale.copy()
        new._rotation = self._rotation.copy()
        new._mv_needs_rebuild = True
        return new

    def _has_scene_element(self):
        return self._elem is not None

    # statics
    @staticmethod
    def zero() -> 'Transform':
        return Transform()


class Spatial:
    @staticmethod
    def quat_rot(quat, vec):  # returns vec rotated by quaternion quat
        return vec + 2.0 * np.cross(quat[0:3], np.cross(quat[0:3], vec) + quat[3] * vec)

    @staticmethod
    def quat_from_vectors(a, b):  # returns a quaternion that rotates a to b
        direction = np.cross(a, b)
        theta = np.acos(np.dot(a, b))
        w = np.cos(theta / 2.0)
        quat = np.empty((1, 4))
        quat[0:3] = direction * np.sin(theta / 2.0)
        quat[3] = w
        return quat

    @staticmethod
    def from_quaternion(quat) -> 'Spatial':
        spatial = Spatial()
        spatial.transform_by_quaternion(quat)
        return spatial

    def __init__(self, i=None, j=None, k=None, translation=None, scale=None):
        self.i = i
        self.j = j
        self.k = k
        self.translation = translation
        self.scale = scale
        if self.translation is None:
            self.translation = np.array([0, 0, 0])
        if self.i is None:
            self.i = np.array([1, 0, 0])
        if self.j is None:
            self.j = np.array([0, 1, 0])
        if self.k is None:
            self.k = np.array([0, 0, 1])
        if self.scale is None:
            self.scale = np.array([1, 1, 1])

    def align_i(self, new_i):
        quat = Spatial.quat_from_vectors(self.i, new_i)
        self.transform_by_quaternion(quat)

    def align_j(self, new_j):
        quat = Spatial.quat_from_vectors(self.j, new_j)
        self.transform_by_quaternion(quat)

    def align_k(self, new_k):
        quat = Spatial.quat_from_vectors(self.k, new_k)
        self.transform_by_quaternion(quat)

    def spin_about_axis (self, axis, radians):
        quat = np.empty((1, 4))
        quat[0:3] = axis * np.sin(radians / 2.0)
        quat[3] = np.cos(radians / 2.0)
        self.transform_by_quaternion(quat)

    def spin_i (self, radians):
        self.spin_about_axis(self.i, radians)

    def spin_j (self, radians):
        self.spin_about_axis(self.j, radians)

    def spin_k (self, radians):
        self.spin_about_axis(self.k, radians)

    def get_quaternion(self):
        return Spatial.quat_from_vectors(np.array([1, 0, 0]), self.i)

    def transform_by_quaternion(self, quaternion):
        self.i = Spatial.quat_rot(quaternion, self.i)
        self.j = Spatial.quat_rot(quaternion, self.j)
        self.k = Spatial.quat_rot(quaternion, self.k)

    def to_matrix(self):
        mat = np.empty((4, 4))
        i = self.i * self.scale[0]
        j = self.j * self.scale[1]
        k = self.k * self.scale[2]
        mat[0][0] = i[0]
        mat[1][0] = i[1]
        mat[2][0] = i[2]

        mat[0][1] = j[0]
        mat[1][1] = j[1]
        mat[2][1] = j[2]

        mat[0][2] = k[0]
        mat[1][2] = k[1]
        mat[2][2] = k[2]

        mat[0][3] = self.translation[0]
        mat[1][3] = self.translation[1]
        mat[2][3] = self.translation[2]

        mat[3][3] = 1
        return mat

    def get_transform (self) -> Transform:
        t = Transform()
        t.set_rotation(self.get_quaternion())
        t.set_translation(self.translation)
        t.set_scale(self.scale)
        return t

    def copy (self) -> 'Spatial':
        s = Spatial()
        s.i = self.i.copy()
        s.j = self.j.copy()
        s.k = self.k.copy()
        s.translation = self.translation.copy()
        s.scale = self.scale.copy()
        return s