import numpy


def get_normals (vertex_data): # binary vertex data, 3 groups of 3 float 32s represent a triangle
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
        v = vertex_data[ind:ind+9]
        a, b, c = v[0], v[1], v[2] # A
        i, j, k = v[3], v[4], v[5] # B
        x, y, z = v[6], v[7], v[8] # C
        bc = (i - x, j - y, k - z)
        ac = (a - x, a - y, a - z)
        norm = cross(*(bc+ac))
        normals += norm[0] + norm[1] + norm[2]
    return normals
def cross (a, b, c, x, y, z):
    """
    | i j k |
    | a b c | = <a, b, c> x <x, y, z>
    | x y z |
    """
    return numpy.array([b * z - y * c, c * x - z * a, a * y - x * x], dtype='float32')