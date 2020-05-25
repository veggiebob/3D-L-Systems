import sys
import numpy as np


from tremor.core.scene_geometry import Brush, Plane


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
    return plane



def parse_keyvalue(string):
    pair = string.split("\" \"", 1)
    pair[0] = pair[0].replace("\"","",1)
    pair[1] = "".join(pair[1].rsplit("\"",1))
    return pair

def parse_file(filename):
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

def main(filename):
    ents = parse_file(filename)
    for ent in ents:
        if ent["classname"] == "worldspawn": #special case, static geometry
            for brush in ent["brushes"]:
                print(brush.get_vertices())

if __name__ == "__main__":
    main(sys.argv[1])