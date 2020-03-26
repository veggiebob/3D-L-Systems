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
