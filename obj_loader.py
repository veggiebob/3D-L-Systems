import pywavefront
import numpy as np
def load_from_file(filename):
    wav = pywavefront.Wavefront(filename, collect_faces=True)
    verts = np.asarray(wav.vertices)
    verts = verts.flatten()
    return verts