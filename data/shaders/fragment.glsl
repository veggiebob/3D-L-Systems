#version 330

out vec4 outputColor;

varying vec3 fposition;
varying vec3 fnormal;
varying vec3 fcolor;
varying vec3 look;

uniform sampler2D noise_512;
uniform sampler2D cat;

const float ambient = 0.1;

//const vec3 look = vec3(0., 0., 1.);

vec2 getTexPos (vec3 p, vec3 n) {
    //does good approximations for textures on coordinate planes
    return ((p.xz*n.y) + (p.xy*n.z) + (p.yz*n.x));
}
void main()
{
    vec3 col = vec3(1.0);
//    float diffuse = max(dot(look, fnormal), 0.);
//    float specular = pow(max(dot(look, reflect(fnormal, -look)), 0.), 4.);
//    col *= (ambient + diffuse * 0.5 + specular * 0.3);
    outputColor = vec4(col, 1.);
}