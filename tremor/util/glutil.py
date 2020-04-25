from OpenGL.GL import *


def log_capabilities():
    print("OPENGL VERSION: ", glGetIntegerv(GL_MAJOR_VERSION), ".", glGetIntegerv(GL_MINOR_VERSION), sep="")
    caps = {
        GL_MAX_TEXTURE_SIZE,
        GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
        GL_MAX_CUBE_MAP_TEXTURE_SIZE,
        GL_MAX_VIEWPORT_DIMS,
        GL_MAX_PATCH_VERTICES,
        GL_MAX_UNIFORM_BLOCK_SIZE,
        GL_MAX_UNIFORM_BUFFER_BINDINGS,
        GL_MAX_UNIFORM_LOCATIONS,
        GL_MAX_CULL_DISTANCES
    }
    for cap in caps:
        print(cap.name + " = " + str(glGetIntegerv(cap)))
