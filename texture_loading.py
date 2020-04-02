from typing import Dict

import PIL, os, yaml
import numpy as np
from PIL import Image

from uniforms import Texture

TEXTURES:Dict[str, Texture] = {}
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
acceptable_file_types = ['bmp', 'png', 'jpg', 'jpeg', 'ppm']

# numpy has it's own flatten lol
def iterable(p):
    try:
        iter(p)
    except TypeError:
        return False
    return True


def flatten(l):  # flatten any-type iterables
    if iterable(l):
        index = -1
        for p in iter(l):
            index += 1
            if iterable(p):
                l = l[:index] + flatten(p) + l[index + 1:]
        return l
    else:
        return l


def get_image_data(filepath):
    try:
        img = Image.open(filepath)
    except PIL.UnidentifiedImageError as e:
        print(e)
        return
    return np.array(img, dtype='float32')

def load_texture(filepath, name:str=None, config:dict={}):
    if name is None: name = filepath
    data = get_image_data(filepath)
    width = len(data[0])
    height = len(data)
    TEXTURES[name] = Texture(data.flatten(), name, width, height, **config)


def load_all_textures(path='./data/textures', config:dict={}):
    files = os.listdir(path)
    for f in files:
        try:
            end = f[f.index('.')+1:]
        except ValueError:
            continue
        if not end in acceptable_file_types:
            continue
        filename = f[:f.index('.')]
        print('loaded texture %s'%filename)
        load_texture('%s/%s'%(path, f), filename, config[filename] if filename in config else {})

if __name__ == '__main__':
    load_all_textures()