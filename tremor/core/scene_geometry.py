import numpy as np
import math

from tremor.math.vertex_math import norm_vec3


def center_of_mass(points: np.array) -> np.array:
    if len(points) == 0:
        raise Exception('wtf')
    x_accum = 0
    y_accum = 0
    z_accum = 0
    for point in points:
        x_accum += point[0]
        y_accum += point[1]
        z_accum += point[2]
    n = len(points)
    return np.array([x_accum, y_accum, z_accum]) / n


class Plane:
    def __init__(self, point: np.ndarray, normal: np.ndarray):
        self.point = point
        self.normal = norm_vec3(normal)

    def point_dist(self, point: np.ndarray):
        return self.normal.dot(point - self.point)


    def intersect_point(self, p1: "Plane", p2: "Plane"):
        # n1 dot n2 cross n3 == 0, single point of intersection
        # n1 dot n2 cross n3 != 0, no points or infinite points of intersection
        a = p2.normal.dot(np.cross(self.normal, p1.normal))
        if a == 0:
            #print("no single point intersection")
            return None
        A = np.array([
            self.normal,
            p1.normal,
            p2.normal
        ])
        B = np.array([
            self.normal.dot(self.point),
            p1.normal.dot(p1.point),
            p2.normal.dot(p2.point)
        ])
        x = np.linalg.solve(A, B)
        return x




class Brush:

    def __init__(self, planes):
        self.planes = planes

    def point_in_brush(self, point):
        for p in self.planes:
            if p.point_dist(point) > 0:
                return False
        return True
        pass

    def get_vertices(self):
        all_points = []
        i = 0
        for p1 in self.planes:
            i += 1
            p1_points = []
            j = 0
            for p2 in self.planes:
                j += 1
                #if i > j:
                #    continue
                k = 0
                for p3 in self.planes:
                    k += 1
                    if j > k:
                        continue
                    point = p1.intersect_point(p2, p3)
                    if point is not None:
                        #print(i,j,k)
                        p1_points.append(point)
            com = center_of_mass(p1_points)
            vals = []
            tangent_vec = p1_points[0] - com
            quad_1 = []
            quad_2 = []
            quad_3 = []
            quad_4 = []
            for i in range(0, len(p1_points)):
                point = p1_points[i] - com
                values = (p1.point_dist(np.cross(tangent_vec, point) + com), tangent_vec.dot(point))
                if values[0] >= 0:
                    if values[1] >= 0:
                        quad_1.append(i)
                    else:
                        quad_2.append(i)
                else:
                    if values[1] < 0:
                        quad_3.append(i)
                    else:
                        quad_4.append(i)
                vals.append(values)
            quad_1.sort(key=lambda x: (-1 if vals[x][0] < 0 else 1) * vals[x][1], reverse=True)
            quad_2.sort(key=lambda x: (-1 if vals[x][0] < 0 else 1) * vals[x][1], reverse=True)
            quad_3.sort(key=lambda x: (-1 if vals[x][0] < 0 else 1) * vals[x][1], reverse=True)
            quad_4.sort(key=lambda x: (-1 if vals[x][0] < 0 else 1) * vals[x][1], reverse=True)
            all_points.append([p1_points[p] for p in quad_1 + quad_2 + quad_3 + quad_4])
        return all_points

    def make_data(self):
        vertices = self.get_vertices()
        tris = np.empty(0, dtype='float32')
        normals = np.empty(0, dtype='float32')

        for j in range(len(vertices)):
            face = vertices[j]
            fan_point = face[0]
            if len(face) == 2:
                continue
            if len(face) == 3:
                tris = np.append(tris, face)
            for i in range(2, len(face)):
                v0 = face[i - 1]
                v1 = face[i]
                tris = np.append(tris, [fan_point, v0, v1])
                norm = self.planes[j].normal
                normals = np.append(normals, [norm, norm, norm])
        return tris, normals


if __name__ == "__main__":
    p1 = Plane(np.array([0, 0, 0]), np.array([0, -1, 0]))
    p2 = Plane(np.array([0, 0, 0]), np.array([-1, 0, 0]))
    p3 = Plane(np.array([0, 0, 0]), np.array([0, 0, -1]))
    p4 = Plane(np.array([1, 1, 1]), np.array([0, 1, 0]))
    p5 = Plane(np.array([1, 1, 1]), np.array([1, 0, 0]))
    p6 = Plane(np.array([1, 1, 1]), np.array([0, 0, 1]))
    b = Brush([p1, p2, p3, p4, p5, p6])
    tris, normals = b.make_data()
    print("H")
