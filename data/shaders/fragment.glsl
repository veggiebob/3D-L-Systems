#version 330

out vec4 outputColor;

in vec3 fposition;
in vec3 fnormal;
in vec3 fcolor;

uniform sampler2D noise_512;
uniform sampler2D cat;

const float ambient = 0.1;

const vec3 look = vec3(0., 0., 1.);

vec2 getTexPos (vec3 p, vec3 n) {
    //does good approximations for textures on coordinate planes
    return ((p.xz*n.y) + (p.xy*n.z) + (p.yz*n.x));
}
void main()
{
    vec3 col = fcolor;
    float diffuse = max(dot(look, fnormal), 0.);
//    diffuse = max(diffuse, 1.0);
    float specular = pow(max(dot(look, reflect(fnormal, -look)), 0.), 4.);
    col *= (ambient + diffuse * 0.5 + specular * 0.8);
    outputColor = vec4(col, 1.);
}