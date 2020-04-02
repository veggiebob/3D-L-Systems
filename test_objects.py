import numpy as np

from game_object import GameObject
from vertex_math import *

def generate_sphere_stl (thetaRes=40, phiRes=40):
    vertices = np.array([], dtype='float32')
    phiC = np.pi / phiRes # map phi index to phi
    thetaC = 2 * np.pi / thetaRes # map theta index to theta
    for iphi in range(phiRes):
        phi = iphi * phiC
        nphi = phi + phiC
        for itheta in range(thetaRes):
            theta = itheta * thetaC
            ntheta = theta + thetaC
            bl = sphere_coords(phi, theta)
            br = sphere_coords(phi, ntheta)
            tl = sphere_coords(nphi, theta)
            tr = sphere_coords(nphi, ntheta)
            vertices = concat(
                vertices,
                concat(bl, tl, br),
                concat(br, tl, tr)
            )
    return vertices

def generate_cone_stl ():
    vertices = np.array([], dtype='float32')
    height = np.sqrt(3) / 2
    top = np.array([0, height, 0], dtype='float32')
    bottom = np.array([0, 0, 0], dtype='float32')
    res = 30
    for a in range(res + 1):
        ang = a / res * 2 * np.pi
        nang = (a+1) / res * 2 * np.pi
        v = sphere_coords(np.pi / 2, ang)
        nv = sphere_coords(np.pi / 2, nang)
        vertices = concat(
            vertices,
            v, nv, top,
            nv, v, bottom
        )
    return vertices

def sphere_coords (phi: float, theta: float):
    return np.array([
        np.cos(theta) * np.sin(phi),
        np.cos(phi),
        np.sin(theta) * np.sin(phi)
    ], dtype='float32')

def generate_box_stl ():
    # except everything is lhr :(
    return np.array(
        [
            -1.0, -1.0, -1.0,
            -1.0, -1.0, 1.0,
            -1.0, 1.0, 1.0,

            -1.0, 1.0, -1.0,
            1.0, 1.0, -1.0,
            -1.0, -1.0, -1.0,

            1.0, -1.0, 1.0,
            -1.0, -1.0, -1.0,
            1.0, -1.0, -1.0,

            1.0, 1.0, -1.0,
            1.0, -1.0, -1.0,
            -1.0, -1.0, -1.0,

            -1.0, -1.0, -1.0,
            -1.0, 1.0, 1.0,
            -1.0, 1.0, -1.0,

            1.0, -1.0, 1.0,
            -1.0, -1.0, 1.0,
            -1.0, -1.0, -1.0,

            -1.0, 1.0, 1.0,
            -1.0, -1.0, 1.0,
            1.0, -1.0, 1.0,

            1.0, 1.0, 1.0,
            1.0, -1.0, -1.0,
            1.0, 1.0, -1.0,

            1.0, -1.0, -1.0,
            1.0, 1.0, 1.0,
            1.0, -1.0, 1.0,

            1.0, 1.0, 1.0,
            1.0, 1.0, -1.0,
            -1.0, 1.0, -1.0,

            1.0, 1.0, 1.0,
            -1.0, 1.0, -1.0,
            -1.0, 1.0, 1.0,

            1.0, 1.0, 1.0,
            -1.0, 1.0, 1.0,
            1.0, -1.0, 1.0
        ],
        dtype='float32'
    )