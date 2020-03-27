import numpy


def get_normals(vertex_data):  # binary vertex data, 3 groups of 3 float 32s represent a triangle
    """
    a______b
     \    /
      \  /
       \/
       c

    assume triangle abc has a normal facing OUT of the screen
    that is, the vertices are in the order (c, b, a), (b, a, c), or (a, c, b)
    using RHR, (b - c) x (a - c) gives us the normal direction
    """
    normals = numpy.array([], dtype='float32')
    for ind in range(0, len(vertex_data), 9):
        v = vertex_data[ind:ind + 9]
        a, b, c = v[0], v[1], v[2]  # A
        i, j, k = v[3], v[4], v[5]  # B
        x, y, z = v[6], v[7], v[8]  # C
        bc = (i - x, j - y, k - z)
        ac = (a - x, a - y, a - z)
        norm = cross(*(bc + ac))
        normals = numpy.append(normals, norm)
    return normals

def cross(a, b, c, x, y, z):
    """
    | i j k |
    | a b c | = <a, b, c> x <x, y, z>
    | x y z |
    """
    return numpy.array([b * z - y * c, c * x - z * a, a * y - x * x], dtype='float32')


def cross_array(v1, v2):
    return cross(v1[0], v1[1], v1[2], v2[0], v2[1], v2[2])

def concat (*args):
    arr = numpy.array([], dtype='float32')
    for a in args:
        arr = numpy.append(arr, a)
    return arr

class ModelOp:
    @staticmethod
    def scale (model, scale_v:numpy.ndarray):
        nm = numpy.array(model, dtype='float32')
        nm[::3] = model[::3] * scale_v[0] # x
        nm[1::3] = model[1::3] * scale_v[1] # y
        nm[2::3] = model[2::3] * scale_v[2] # z
        return nm
    @staticmethod
    def translate (model:numpy.ndarray, trans_v:numpy.ndarray):
        nm = numpy.array([], dtype='float32')
        nm[::3] = model[::3] + trans_v[0]
        nm[1::3] = model[1::3] + trans_v[1]
        nm[2::3] = model[2::3] + trans_v[2]
        return nm
