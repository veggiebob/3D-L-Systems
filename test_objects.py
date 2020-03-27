import numpy as np
from vertex_math import *
def generate_sphere ():
    vertices = np.array([], dtype='float32')
    thetaRes = 40 # number of longitudinal lines
    phiRes = 40 # number of latitude lines
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
                concat(tl, tr, br)
            )
    return vertices

def generate_cone ():
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