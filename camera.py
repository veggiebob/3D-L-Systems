import numpy as np
def spin (time): # puts camera on unit circle, spinning around the origin
    cam = np.array([
        np.sin(time * 0.01),
        1,
        np.cos(time * 0.01)
    ])
    v = (np.cos(time * 0.005) + 1) / 2 - 0.5
    cam[0] *= v
    cam[2] *= v
    cam[1] *= np.sin(time * 0.005)
    return cam

def spin_xz (time): # puts camera on unit circle, spinning around the origin
    cam = np.array([
        np.sin(time * 0.01),
        1,
        np.cos(time * 0.01)
    ])
    return cam

