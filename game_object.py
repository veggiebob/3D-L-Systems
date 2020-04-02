from typing import List

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
class Attribute:
    def __init__(self, location=0, name="none", vbo_id=0):
        self.name = name
        self.location = location
        self.vbo_id = vbo_id
class Attributes:
    def __init__(self):
        self.attributes:List[Attribute] = []
    def name_in_attributes (self, name:str) -> bool:
        for a in self.attributes:
            if a.name == name:
                return True
        return False
    def location_in_attributes (self, location) -> bool:
        for a in self.attributes:
            if a.location == location:
                return True
        return False
    def vbo_id_in_attributes (self, vbo_id:int):
        for a in self.attributes:
            if a.vbo_id == vbo_id:
                return True
        return False
    def add_attribute(self, name:str, location, vbo_id:int):
        if not self.name_in_attributes(name) and not self.location_in_attributes(location) and not self.vbo_id_in_attributes(vbo_id):
            self.attributes.append(Attribute(name=name, location=location, vbo_id=vbo_id))
class RenderableObject:
    def __init__(self): # todo: add uniform control
        self.vaoID = GL.glGenVertexArrays(1)
        self.attributes = Attributes()
        self.vertex_count = 0
        self.face_count = 0
        # 2 things to do on init:
        #   - bind_indices_vbo()
        #   - bind_float_attribute_vbo()

    def bind_indices_vbo(self, data): # must be 4 byte ints
        # print('received data %s'%data)
        self.bind_vao()
        self.face_count = len(data) / 3
        vbo_id = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, vbo_id)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW)
        self.unbind_vao()
        # * apparently you don't unbind this vbo because it's SPECIAL

    def bind_float_attribute_vbo (self, data, attribute_name:str, static: bool, program): # must be 4 byte floats
        # print('received data %s' % data)
        self.bind_vao()
        if attribute_name=='position': # todo: is there a better way to do this?
            self.vertex_count = int(len(data) / 3)
        vbo_id = GL.glGenBuffers(1)
        location = GL.glGetAttribLocation(program, attribute_name)
        # print('location isss %s for %s'%(location, attribute_name))
        self.attributes.add_attribute(name=attribute_name, location=location, vbo_id=vbo_id)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_id) # bind it
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW if static else GL.GL_DYNAMIC_DRAW) # add the data into it
        GL.glVertexAttribPointer(location, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None) # tell it how to parse it
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0) # unbind it
        self.unbind_vao()


    def render (self):
        # https://github.com/TheThinMatrix/OpenGL-Tutorial-3/blob/master/src/renderEngine/Renderer.java #render
        self.bind_vao()
        for a in self.attributes.attributes:
            GL.glEnableVertexAttribArray(a.location)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, a.vbo_id) # whyyyy
            GL.glVertexAttribPointer(a.location, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None) # this makes no sense
        # GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count) # say goodbye to this
        GL.glDrawElements(GL.GL_TRIANGLES, self.vertex_count * 9, GL.GL_UNSIGNED_INT, None)
        for a in self.attributes.attributes:
            GL.glDisableVertexAttribArray(a.location)
        self.unbind_vao()



    def bind_vao (self):
        GL.glBindVertexArray(self.vaoID)

    def unbind_vao (self):
        GL.glBindVertexArray(0)