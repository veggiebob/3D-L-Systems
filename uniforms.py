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

gl_compressed_format: Dict[int, int] = {
    GL_R: GL_COMPRESSED_RED,
    GL_RG: GL_COMPRESSED_RG,
    GL_RGB: GL_COMPRESSED_RGB,
    GL_RGBA: GL_COMPRESSED_RGBA,
    GL_SRGB: GL_COMPRESSED_SRGB,
    GL_SRGB_ALPHA: GL_COMPRESSED_SRGB_ALPHA
    # exotic formats omitted
}


class Uniform:
    def __init__(self, name: str, loc=None, values: list = None, u_type: str = ''):
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
            print('no value set for uniform %s' % self.name)
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
    for n, u in uniforms.items():
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

    def __init__(self, data: np.ndarray, name: str, width: int = 1, height: int = 1, sample_mode=GL_LINEAR,
                 clamp_mode=GL_CLAMP_TO_EDGE, img_format=GL_RGB):
        self.data = data
        self.width = width if width > 0 else len(self.data[0])
        self.height = height if height > 0 else len(self.data)
        self.name = name
        self.index = Texture.index
        self.sample_mode = sample_mode
        self.clamp_mode = clamp_mode
        self.format = img_format
        self.texture = None
        self.init()
        Texture.index += 1  # increment for other textures

    def set_texture(self):
        # https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glTexImage2D.xhtml
        glTexImage2D(
            GL_TEXTURE_2D,  # target
            0,  # level
            gl_compressed_format[self.format],  # internalformat
            self.width,  # width
            self.height,  # height
            0,  # border
            self.format,  # format
            GL_UNSIGNED_BYTE,  # type
            self.data,  # pixels
        )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.sample_mode)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.sample_mode)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.clamp_mode)  # x
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.clamp_mode)  # y
        glGenerateMipmap(GL_TEXTURE_2D)

    def bind(self):
        glActiveTexture(GL_TEXTURE0 + self.index)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def init(self):
        self.texture = glGenTextures(1)
        self.bind()
        # glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        self.set_texture()
        # glGenerateMipmap(GL_TEXTURE_2D)

    def update(self, shader):
        glActiveTexture(GL_TEXTURE0 + self.index)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glUniform1i(
            glGetUniformLocation(shader, self.name),
            self.index
        )

    def update_data(self, data: np.ndarray, width: int = 0, height: int = 0):
        if width > 0:
            self.width = width
        if height > 0:
            self.height = height
        self.data = data
        self.bind()
        self.set_texture()

    def transfer(self, other_texture: 'Texture'):
        self.set_format(other_texture.format)
        self.sample_mode = other_texture.sample_mode
        self.clamp_mode = other_texture.clamp_mode
        self.update_data(other_texture.data, other_texture.width, other_texture.height)

    def set_format(self, img_format):
        self.format = img_format

    def set_sampler(self, sampler):
        self.sample_mode = sampler.sample_mode
        self.clamp_mode = sampler.clamp_mode
