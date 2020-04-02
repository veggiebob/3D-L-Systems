import numpy as np
def spin (time): # puts camera on unit circle, spinning around the origin
    cam = np.array([
        np.sin(time * 0.01),
        1,
        np.cos(time * 0.01)
    ])
    cam[0] *= np.cos(time * 0.005)
    cam[2] *= np.cos(time * 0.005)
    cam[1] *= np.sin(time * 0.005)
    return cam