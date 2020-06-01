import ctypes
from typing import List, Dict

import OpenGL.GL as gl

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
    def __init__ (self, attachments:List[gl.GLenum], resolution=(512,512)): # for example, GL_COLOR_ATTACHMENT0
        self.fbo = gl.glGenFramebuffers()
        self.attachments = attachments
        self.textures:Dict[gl.GLenum, TextureUnit] = {}
        self.resolution = resolution # bleh

        #init
        self.bind()
        for a in self.attachments:
            gl.glDrawBuffer(a)
        # assume they all are textures as well, no renderbuffers
        for a in self.attachments:
            self.set_attachment_texture(a)
        self.unbind()
    def get_attachment_texture (self, attachment=gl.GL_COLOR_ATTACHMENT0) -> TextureUnit:
        if attachment in self.textures.keys():
            return self.textures[attachment]
        else:
            raise Exception(f"{attachment} is not an attachment in the FBO!")
    def set_attachment_texture (self, attachment):
        from tremor.loader.gltf_loader import get_default_sampler
        self.textures[attachment] = TextureUnit.generate_texture()
        self.textures[attachment].bind_tex2d(ctypes.c_void_p(0), self.resolution[0], self.resolution[1], gl.GL_RGB, get_default_sampler())
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, attachment, self.textures[attachment].unit, 0)
    def bind (self):
        gl.glBindFramebuffer(self.fbo)
    def unbind (self):
        gl.glBindFramebuffer(0)
    def render (self):
        self.bind()
        gl.glViewport(0, 0, self.resolution[0], self.resolution[1])