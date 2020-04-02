import OpenGL
import OpenGL.GL as GL
"""
todo steps:
    initialization:
     - create a vao
     - create/update vbos
        - bind vao
        - generate vbo
        - bind vbo
        - add data to vbo
        - unbind vbo*
        - unbind vao
    rendering:
     - bind vao
     - enable vao
     - draw it
     - disable vao
     - unbind it
"""
class GameObject:
    def __init__(self):
        self.vaoID = GL.glGenVertexArrays(1)
        self.attribute_indices = []
        self.vertex_count = 0
        # 2 things to do on init:
        #   - bind_indices_vbo()
        #   - bind_float_attribute_vbo()

    def bind_indices_vbo(self, data): # must be 4 byte ints
        # print('received data %s'%data)
        self.bind_vao()
        id = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, id)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW)
        self.vertex_count = int(len(data) / 3)
        # apparently you don't unbind this vbo because it's SPECIAL
        self.unbind_vao()

    def bind_float_attribute_vbo (self, data, attribute_index:int, static: bool): # must be 4 byte floats
        # print('received data %s' % data)
        self.bind_vao()
        vbo_id = GL.glGenBuffers(1)
        if not attribute_index in self.attribute_indices:
            self.attribute_indices.append(attribute_index)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_id) # bind it
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW if static else GL.GL_DYNAMIC_DRAW) # add the data into it
        GL.glVertexAttribPointer(attribute_index, 3, GL.GL_FLOAT, False, 0, 0) # tell it how to parse it
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0) # unbind it
        self.unbind_vao()


    def render (self):
        # https://github.com/TheThinMatrix/OpenGL-Tutorial-3/blob/master/src/renderEngine/Renderer.java #render
        self.bind_vao()
        for ind in self.attribute_indices:
            GL.glEnableVertexAttribArray(ind)
        # GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count) # say goodbye to this
        GL.glDrawElements(GL.GL_TRIANGLES, self.vertex_count, GL.GL_UNSIGNED_INT, 0)
        for ind in self.attribute_indices:
            GL.glDisableVertexAttribArray(ind)
        self.unbind_vao()



    def bind_vao (self):
        GL.glBindVertexArray(self.vaoID)

    def unbind_vao (self):
        GL.glBindVertexArray(0)