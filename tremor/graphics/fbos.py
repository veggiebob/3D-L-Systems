import ctypes
from typing import List, Dict

import OpenGL.GL as gl
from OpenGL.GL.framebufferobjects import *

from tremor.graphics import screen_utils
from tremor.graphics.surfaces import TextureUnit

"""
steps to make a cool fbo:
fbo = glGenFramebuffers()
glBindFramebuffer(GL_FRAMEBUFFER, fbo) # GL_FRAMEBUFFER is read/write, this binds it to the context
glDrawBuffer(GL_COLOR_ATTACHMENT0) # this adds a draw buffer, which is an attachment to the fbo

# when it is bound and you have a texture:
glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texture, 0) # tells it to render to a texture, and which attachment you want it to render to
# you can also attach render buffers

to render to a fbo:
glBindTexture(GL_TEXTURE_2D, 0) # just to make sure? please don't have this
glBindFramebuffer(GL_FRAMEBUFFER, fbo)
glViewport, glUseProgram, etc.
glBindFramebuffer(GL_FRAMEBUFFER, 0) # go back to screen
"""
class FBO:
    """
    For my implementation, since fbos render to a texture, they should be their own objects. They should always render to their own texture, and therefore have their own texture.
    """
    # uniform enum, much like MaterialTexture
    REFLECTION = 'FBOreflection'
    FINAL_RENDER_OUTPUT = 'FBOscreen'
    OTHER = 'FBOother'
    def __init__ (self, name:str, attachment_textures:List[gl.GLenum], attachment_renderbuffers:List[gl.GLenum], resolution=(512,512), fbo_type=None): # for example, attachements=[GL_COLOR_ATTACHMENT0], fbo_type=FBO.REFLECTION
        if not bool(glGenFramebuffers):
            raise Exception('You need glGenFramebuffers')
        self.name = name
        self.fbo = glGenFramebuffers(1)
        self.fbo_type = fbo_type if fbo_type is not None else FBO.OTHER
        self.attachment_textures = attachment_textures
        self.textures:Dict[gl.GLenum, TextureUnit] = {}
        self.resolution = resolution # bleh

        #init
        self.bind()
        for a in self.attachment_textures + attachment_renderbuffers:
            if a == GL_DEPTH_ATTACHMENT:
                continue
                # gl.glDrawBuffer(gl.GL_NONE)
            else:
                gl.glDrawBuffer(a)
        # assume they all are textures as well, no renderbuffers
        for a in attachment_textures:
            self.set_attachment_texture(a)
        for a in attachment_renderbuffers:
            if a == GL_DEPTH_ATTACHMENT:
                self.set_attachment_renderbuffer(a, format=gl.GL_DEPTH_COMPONENT32)
            else:
                self.set_attachment_renderbuffer(a)
        self.unbind()
    def get_attachment_texture (self, attachment=gl.GL_COLOR_ATTACHMENT0) -> TextureUnit:
        if attachment in self.textures.keys():
            return self.textures[attachment]
        else:
            raise Exception(f"{attachment} is not an attachment in the FBO!")
    def set_attachment_texture (self, attachment):
        from tremor.loader.gltf_loader import get_default_sampler
        self.textures[attachment] = TextureUnit.generate_texture()
        samp = get_default_sampler()
        samp.minFilter = gl.GL_LINEAR
        self.textures[attachment].bind_tex2d(ctypes.c_void_p(0), self.resolution[0], self.resolution[1], gl.GL_RGB, samp)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, attachment, self.textures[attachment].unit, 0)
    def set_attachment_renderbuffer (self, attachment, format=gl.GL_RGBA8):
        # we don't need to keep these around because you can't even use them
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, format, self.resolution[0], self.resolution[1])
        glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER,
            attachment,
            GL_RENDERBUFFER,
            rbo
        )
    def bind (self):
        gl.glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
    def unbind (self):
        gl.glBindFramebuffer(GL_FRAMEBUFFER, 0)
    def prepare_render (self):
        self.bind()
        gl.glViewport(0, 0, self.resolution[0], self.resolution[1])
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # for a in self.attachment_textures:
        #     gl.glDrawBuffer(a)
    def return_to_screen (self):
        self.unbind()
        gl.glViewport(0, 0, screen_utils.WIDTH, screen_utils.HEIGHT)


GLOBAL_FBOS:List[FBO] = [
]
def initialize_global_fbos ():
    GLOBAL_FBOS.append(
        FBO(
            name="reflection",
            attachment_textures=[GL_COLOR_ATTACHMENT0],
            attachment_renderbuffers=[GL_DEPTH_ATTACHMENT],
            resolution=(512, 512),
            fbo_type=FBO.REFLECTION
        )
    )
    GLOBAL_FBOS.append(
        FBO(
            name="screen",
            attachment_textures=[GL_COLOR_ATTACHMENT0],
            attachment_renderbuffers=[GL_DEPTH_ATTACHMENT],
            resolution=screen_utils.dim(),
            fbo_type=FBO.FINAL_RENDER_OUTPUT
        )
    )
    pass
def find_fbo_by_type (fbo_type) -> FBO:
    for fbo in GLOBAL_FBOS:
        if fbo.fbo_type == fbo_type:
            return fbo
    raise Exception(f"Could not find fbo {fbo_type}")

def find_fbo_by_name (fbo_name) -> FBO:
    for f in GLOBAL_FBOS:
        if fbo_name == f.name:
            return f
    raise Exception(f"Could not find fbo by name {fbo_name}")
