import struct
from typing import List

import numpy as np

class RawModelVertex:
    def __init__(self, index: int):
        self.index = index

    @staticmethod
    def size():
        return struct.calcsize("<i")

    def serialize(self):
        return struct.pack("<i", self.index)

    @staticmethod
    def deserialize(contents):
        return RawModelVertex(*struct.unpack('<i', contents))


class RawVertex:
    def __init__(self, point: np.ndarray, normal: np.ndarray, texcoord: np.ndarray):
        self.point = point
        self.normal = normal
        self.texcoord = texcoord

    @staticmethod
    def size():
        return struct.calcsize('<ffffffff')

    def serialize(self):
        return struct.pack('<ffffffff', *self.point, *self.normal, *self.texcoord)

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack('<ffffffff', contents)
        return RawVertex(np.array(stuf[0:3], dtype='float32'), np.array(stuf[3:6], dtype='float32'),
                         np.array(stuf[6:8], dtype='float32'))


class RawPlane:
    def __init__(self, point: np.ndarray, normal: np.ndarray):
        self.point = point
        self.normal = normal

    def serialize(self):
        return struct.pack("<ffffff", *self.point, *self.normal)

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack("<ffffff", contents)
        return RawPlane(np.array(stuf[0:3], dtype='float32'), np.array(stuf[3:6], dtype='float32'))


class RawFace:
    def __init__(self, textureidx: int, vertstart: int, vertcount: int, meshvertstart: int, meshvertcount: int,
                 normal: np.ndarray):
        self.textureidx = textureidx
        self.vertstart = vertstart
        self.vertcount = vertcount
        self.meshvertstart = meshvertstart
        self.meshvertcount = meshvertcount
        self.normal = normal

    def serialize(self):
        return struct.pack("<iiiIIfff", self.textureidx, self.vertstart, self.vertcount, self.meshvertstart,
                           self.meshvertcount, self.normal[0], self.normal[1], self.normal[2])

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack("<iiiIIfff", contents)
        return RawFace(stuf[0], stuf[1], stuf[2], stuf[3], stuf[4], np.array(stuf[5:8], dtype='float32'))

    @staticmethod
    def size():
        return struct.calcsize("<iiiIIfff")


class RawTexture:
    def __init__(self, name: bytes):
        if len(name) > 64:
            name = name[0:64]  # :)
        self.name = name

    def serialize(self):
        return struct.pack("<64s", self.name)

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack("<64s", contents)
        return RawTexture(*stuf)

    @staticmethod
    def size():
        return struct.calcsize("<64s")


class RawBrush:
    def __init__(self, content_flags: int, first_brush_side: int, brush_side_count: int):
        self.content_flags = content_flags
        self.first_brush_side = first_brush_side
        self.brush_side_count = brush_side_count


class RawBrushSide:
    def __init__(self, plane_index: int, surface_flags: int):
        self.plane_index = plane_index
        self.surface_flags = surface_flags


class RawModel:
    # todo brushes
    def __init__(self, face_start: int, face_count: int):
        self.face_start = face_start
        self.face_count = face_count

    @staticmethod
    def size():
        return struct.calcsize("<ii")

    def serialize(self):
        return struct.pack("<ii", self.face_start, self.face_count)

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack("<ii", contents)
        return RawModel(*stuf)


class RawChunkDirectoryEntry:
    def __init__(self, type: int, version: int, compression: int, start: int, length: int):
        self.type = type
        self.version = version
        self.compression = compression
        self.start = start
        self.length = length

    @staticmethod
    def size():
        return struct.calcsize("<iiiii")

    def serialize(self):
        return struct.pack("<iiiii", self.type, self.version, self.compression, self.start, self.length)

    @staticmethod
    def deserialize(contents):
        stuf = struct.unpack("<iiiii", contents)
        return RawChunkDirectoryEntry(*stuf)


class VertexChunk:
    def __init__(self, vertexlist: List[RawVertex]):
        self.vertexlist = vertexlist

    def length_bytes(self):
        return len(self.vertexlist) * RawVertex.size()

    def serialize(self):
        single_length = RawVertex.size()
        length = len(self.vertexlist) * single_length
        buffer = bytearray(length)
        c = 0
        for vertex in self.vertexlist:
            buffer[c:c + single_length] = vertex.serialize()
            c += single_length
        return buffer

    @staticmethod
    def deserialize(chunk):
        single_length = RawVertex.size()
        chunk_len_elem = len(chunk) // single_length
        verts = []
        for c in range(0, chunk_len_elem):
            verts.append(RawVertex.deserialize(chunk[c * single_length:c * single_length + single_length]))
        return VertexChunk(verts)
    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return VertexChunk.deserialize(buf[dir.start:dir.start+dir.length])


class ModelVertexChunk:
    def __init__(self, modelverts: List[RawModelVertex]):
        self.modelverts = modelverts

    def length_bytes(self):
        return len(self.modelverts) * RawModelVertex.size()

    def serialize(self):
        single_length = RawModelVertex.size()
        length = len(self.modelverts) * single_length
        buffer = bytearray(length)
        for c in range(0, len(self.modelverts)):
            buffer[c * single_length: c * single_length + single_length] = self.modelverts[c].serialize()
        return buffer

    @staticmethod
    def deserialize(chunk):
        single_length = RawModelVertex.size()
        length = len(chunk) // single_length
        mverts = []
        for i in range(0, length):
            mverts.append(RawModelVertex.deserialize(chunk[i * single_length: i * single_length + single_length]))
        return ModelVertexChunk(mverts)

    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return ModelVertexChunk.deserialize(buf[dir.start:dir.start + dir.length])


class FaceChunk:
    def __init__(self, faces: List[RawFace]):
        self.faces = faces

    def length_bytes(self):
        return len(self.faces) * RawFace.size()

    def serialize(self):
        single_length = RawFace.size()
        length = len(self.faces) * single_length
        buffer = bytearray(length)
        c = 0
        for face in self.faces:
            buffer[c:c + single_length] = face.serialize()
            c += single_length
        return buffer

    @staticmethod
    def deserialize(chunk):
        single_length = RawFace.size()
        chunk_len_elem = len(chunk) // single_length
        faces = []
        for c in range(0, chunk_len_elem):
            faces.append(RawFace.deserialize(chunk[c * single_length : c * single_length + single_length]))
        return FaceChunk(faces)

    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return FaceChunk.deserialize(buf[dir.start:dir.start+dir.length])


class ModelChunk:
    def __init__(self, models: List[RawModel]):
        self.models = models

    def length_bytes(self):
        return len(self.models) * RawModel.size()

    def serialize(self):
        single_length = RawModel.size()
        length = len(self.models) * single_length
        buffer = bytearray(length)
        c = 0
        for model in self.models:
            buffer[c:c + single_length] = model.serialize()
            c += single_length
        return buffer

    @staticmethod
    def deserialize(chunk):
        single_length = RawModel.size()
        chunk_len_elem = len(chunk) // single_length
        models = []
        for c in range(0, chunk_len_elem):
            models.append(RawModel.deserialize(chunk[c * single_length:c * single_length + single_length]))
        return ModelChunk(models)

    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return ModelChunk.deserialize(buf[dir.start:dir.start+dir.length])

class TextureChunk:
    def __init__(self, textures: List[RawTexture]):
        self.textures = textures

    def length_bytes(self):
        return len(self.textures) * RawTexture.size()

    def serialize(self):
        single_length = RawTexture.size()
        length = len(self.textures) * single_length
        buffer = bytearray(length)
        c = 0
        for texture in self.textures:
            buffer[c:c + single_length] = texture.serialize()
            c += single_length
        return buffer

    @staticmethod
    def deserialize(chunk):
        single_length = RawTexture.size()
        chunk_len_elem = len(chunk) // single_length
        models = []
        for c in range(0, chunk_len_elem):
            models.append(RawTexture.deserialize(chunk[c * single_length:c * single_length + single_length]))
        return TextureChunk(models)

    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return TextureChunk.deserialize(buf[dir.start:dir.start+dir.length])


class EntityChunk:
    def __init__(self, contents: bytes):
        self.contents = contents

    def length_bytes(self):
        return len(self.contents)

    def serialize(self):
        return self.contents

    @staticmethod
    def deserialize(contents):
        return EntityChunk(contents)

    @staticmethod
    def from_directory(buf, dir: RawChunkDirectoryEntry):
        return EntityChunk.deserialize(buf[dir.start:dir.start+dir.length])


ENTITY_CHUNK_TYPE = b"ENTY"
VERTEX_CHUNK_TYPE = b"VERT"
MESH_VERTEX_CHUNK_TYPE = b"MVER"
FACE_CHUNK_TYPE = b"FACE"
TEXTURE_CHUNK_TYPE = b"TEXT"
PLANE_CHUNK_TYPE = b"PLAN"
MODEL_CHUNK_TYPE = b"MODL"

NUMBER_OF_CHUNKS = 6
VERTEX_CHUNK_INDEX = 0
MODEL_VERTEX_CHUNK_INDEX = 1
FACE_CHUNK_INDEX = 2
MODEL_CHUNK_INDEX = 3
ENTITY_CHUNK_INDEX = 4
TEXTURE_CHUNK_INDEX = 5

HEADER = b'TMF\b\1\0\0\0'
HEADER_SIZE = len(HEADER)