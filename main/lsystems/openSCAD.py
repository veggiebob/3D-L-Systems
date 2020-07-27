from main.core.entity import Entity
from main.lsystems.parser import LSystem, LSystemGenerator
from main.math import vertex_math


def disp_arr (narray, precision=5):
    return '[' + ','.join([(f"%.{precision}f")%a for a in narray]) + ']'
def generate_OpenSCAD_script (entity, output_file=None, detail=10):
    print('generating openscad script . . .')
    script = f"%fn={detail};\n" + """
//slow way to make easy line
module s (start, end, thickness_start, thickness_end) {
    hull () {
        translate(start) sphere(thickness_start);
        translate(end) sphere(thickness_end);
    }
}
    """
    precision = 3
    tree:Entity = entity
    for t in tree.children:
        p1 = t.transform.get_translation()
        p2 = p1 + vertex_math.norm_vec3(t.transform.get_rotation()[0:3]) * t.transform.get_scale()[1]
        thickness = t.transform.get_scale()[0] * 0.4
        script += "\ns(%s, %s, %.3f, %.3f);"%(disp_arr(p1, precision), disp_arr(p2, precision), thickness, thickness)

    if output_file is None:
        return script

    f = open(output_file, 'w')
    f.write(script)
    f.close()
    return True