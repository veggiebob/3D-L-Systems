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


def sphere_coords (phi: float, theta: float):
    return np.array([
        np.cos(theta) * np.sin(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(phi)
    ], dtype='float32')