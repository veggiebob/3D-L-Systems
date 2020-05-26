import sys
import io
from typing import List

import numpy as np
from tremor.core.scene_geometry import Brush, Plane
import struct

from tremor.loader.scene.scene_types import *


def parse_side(string):
    temp = string.split(" ")
    point = []
    points = []
    plane_points = []

    for token in temp:
        if len(points) == 3:
            break
        if token == "(":
            continue
        if token == ")":
            points.append(point)
            point = []
            continue
        point.append(float(token))
    for point in points:
        plane_points.append(np.array([point[1], point[2], point[0]], dtype='float32'))
    plane = Plane.plane_from_points_quake_style(plane_points)
    plane.texture_name = temp[15]
    # todo load scale and offset and rotation, lol
    # todo and flags!
    return plane


def parse_keyvalue(string):
    pair = string.split("\" \"", 1)
    pair[0] = pair[0].replace("\"", "", 1)
    pair[1] = "".join(pair[1].rsplit("\"", 1))
    return pair


def parse_map_file(filename):
    file = open(filename, 'rt', encoding="utf-8")
    in_ent = False
    in_brush = False
    entities = []
    brush_temp = []
    current_ent = {}
    for line in file:
        line = line.strip()
        if line.startswith("//"):
            continue
        print(line)
        if line == "{":
            if not in_ent:
                print("enter ent")
                in_ent = True
            elif in_ent and not in_brush:
                print("enter brush")
                in_brush = True
            elif in_ent and in_brush:
                raise Exception("bad")
            continue
        if line == "}":
            if in_brush:
                print("exit brush")
                in_brush = False
                if "brushes" not in current_ent:
                    current_ent["brushes"] = []
                current_ent["brushes"].append(Brush(brush_temp))
                brush_temp = []
            elif in_ent:
                in_ent = False
                print("exit ent")
                entities.append(current_ent)
                print(current_ent)
                current_ent = {}
            elif not in_ent and not in_brush:
                raise Exception("bad")
            continue
        if in_ent and not in_brush:
            line = parse_keyvalue(line)
            current_ent[line[0]] = line[1]
            continue
        if in_ent and in_brush:
            brush_temp.append(parse_side(line))
    return entities


def format_ents(ents: List[dict]) -> str:
    buf = io.StringIO()
    for ent in ents:
        buf.write("{\n")
        for k, v in ent.items():
            buf.write("\"" + str(k) + "\"" + " " + "\"" + str(v) + "\"\n")
        buf.write("}\n")
    return buf.getvalue()


def main(filename):
    print("compiling map " + filename)
    output_file = open("out.tmb", "w+b")
    output_file.write(HEADER)
    ents = parse_map_file(filename)
    raw_verts = []
    raw_faces = []
    raw_mesh_verts = []
    raw_models = []
    for ent in ents:
        if "brushes" in ent:
            face_start = len(raw_faces)
            face_count = 0
            for brush in ent["brushes"]:
                vertices = brush.get_vertices()
                for j in range(len(vertices)):
                    face = vertices[j]
                    raw_vert_start = len(raw_verts)
                    raw_mesh_start = len(raw_mesh_verts)
                    raw_mesh_count = 0
                    for i in range(0, len(face)):
                        raw_verts.append(
                            RawVertex(face[i], brush.planes[j].normal, np.array([0.0, 0.0], dtype='float32')))
                    for i in range(2, len(face)):
                        raw_mesh_verts.append(RawModelVertex(raw_vert_start))
                        raw_mesh_verts.append(RawModelVertex(raw_vert_start + i - 1))
                        raw_mesh_verts.append(RawModelVertex(raw_vert_start + i))
                        raw_mesh_count += 3
                    raw_faces.append(
                        RawFace(-1, raw_vert_start, len(face), raw_mesh_start, raw_mesh_count, brush.planes[j].normal))
                    face_count += 1
            ent.pop("brushes")
            ent["model"] = "*" + str(len(raw_models))
            raw_models.append(RawModel(face_start, face_count))

    file_loc = HEADER_SIZE + RawChunkDirectoryEntry.size() * NUMBER_OF_CHUNKS + 1
    chunks = [
        (VertexChunk(raw_verts), VERTEX_CHUNK_TYPE),
        (ModelVertexChunk(raw_mesh_verts), MESH_VERTEX_CHUNK_TYPE),
        (FaceChunk(raw_faces), FACE_CHUNK_TYPE),
        (ModelChunk(raw_models), MODEL_CHUNK_TYPE),
        (EntityChunk(bytes(format_ents(ents), 'utf-8')), ENTITY_CHUNK_TYPE)
    ]
    idx = 0
    for c, t in chunks:
        entry = RawChunkDirectoryEntry(int.from_bytes(t, byteorder='little'),
                                       0,
                                       0,
                                       file_loc,
                                       c.length_bytes())
        output_file.seek(HEADER_SIZE + RawChunkDirectoryEntry.size() * idx)
        output_file.write(entry.serialize())
        output_file.seek(entry.start)
        output_file.write(c.serialize())
        file_loc = output_file.seek(0, io.SEEK_CUR) + 1  # 1 pad byte just because ;)
        idx += 1


if __name__ == "__main__":
    main(sys.argv[1])
