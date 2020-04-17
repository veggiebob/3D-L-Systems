from typing import Dict, Callable

from OpenGL.GL import *
from array import array
import numpy as np

# https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glUniform.xhtml
u_types: Dict[str, Callable] = {
    'float': glUniform1f,
    'vec2': glUniform2f,
    'vec3': glUniform3f,
    'vec4': glUniform4f,
    'int': glUniform1i,
    'bool': glUniform1i,
    'ivec2': glUniform2i,
    'ivec3': glUniform3i,
    'mat3': glUniformMatrix3fv,
    'mat4': glUniformMatrix4fv
}


class Uniform:
    def __init__(self, name:str, loc=None, values: list = None, u_type: str = ''):
        self.name = name
        self.loc = loc
        self.values: list = values
        self.u_type: str = u_type

    def get_uniform_func(self) -> Callable:
        return u_types[self.u_type]

    def get_args(self) -> list:
        return [self.loc, ] + self.values

    def call_uniform_func(self, values: list = None) -> None:
        if not values is None:
            self.values = values
        if self.values is None or len(self.values) == 0:
            print('no value set for uniform %s'%self.name)
            return
        self.get_uniform_func()(*self.get_args())


uniforms: Dict[str, Uniform] = {}


def add_uniform(name: str, u_type: str):
    if not u_type in u_types.keys():
        print('uniform type %s is not a valid type' % u_type)
    uniforms[name] = Uniform(
        name=name,
        loc=None,
        values=[],
        u_type=u_type
    )


def update_uniform(name: str, values: list = None):
    check_is_uniform(name)
    uniforms[name].call_uniform_func(values)


def init_uniforms(program):
    for n,u in uniforms.items():
        u.loc = glGetUniformLocation(program, u.name)


def check_is_uniform(name: str) -> bool:  # not a hard stop, but warning
    if not name in uniforms:
        print('%s is not a uniform!' % name)
        return False
    return True


def set_uniform_values(name: str, values: list):
    check_is_uniform(name)
    uniforms[name].values = values


def update_all_uniforms():
    for u in uniforms.values():
        u.call_uniform_func()

# a texture is technically a uniform, of type "sampler2D"
class Texture:
    index = 0
    def __init__ (self, data:np.ndarray, name:str, width:int=1, height:int=1, sample_mode=GL_LINEAR, clamp_mode=GL_CLAMP):
        self.data = data
        self.width = width if width > 0 else len(self.data[0])
        self.height = height if height > 0 else len(self.data)
        self.name = name
        self.index = Texture.index
        self.sample_mode = sample_mode
        self.clamp_mode = clamp_mode
        self.texture = None
        self.init()
        Texture.index += 1 # increment for other textures

    def set_texture(self):
        # https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml
        glTexImage2D(
            GL_TEXTURE_2D, # target
            0, # level
            3, # internalformat
            self.width, # width
            self.height, # height
            0, # border
            GL_RGB, # format
            GL_UNSIGNED_BYTE, # type
            self.data, # pixels
        )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.sample_mode)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.sample_mode)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.clamp_mode)  # x
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.clamp_mode)  # y
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        glGenerateMipmap(GL_TEXTURE_2D)

    def bind (self):
        glActiveTexture(GL_TEXTURE0 + self.index)
        glBindTexture(GL_TEXTURE_2D, self.texture)
    def init(self):
        self.texture = glGenTextures(1)
        self.bind()
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        self.set_texture()
        glGenerateMipmap(GL_TEXTURE_2D)

    def update(self, shader):
        glActiveTexture(GL_TEXTURE0 + self.index)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glUniform1i(
            glGetUniformLocation(shader, self.name),
            self.index
        )

    def update_data(self, data:np.ndarray, width:int=0, height:int=0): # not sure if you actually need to call this ever but we'll see
        if width > 0:
            self.width = width
        if height > 0:
            self.height = height
        self.data = data
        # self.init()
        self.bind()
        self.set_texture()

    def transfer (self, other_texture: 'Texture'):
        self.update_data(other_texture.data, other_texture.width, other_texture.height)

