#version 330

out vec4 outputColor;

varying vec3 fposition;
varying vec3 fnormal;
varying vec3 fcolor;

uniform sampler2D noise_512;
uniform sampler2D cat;

vec2 getTexPos (vec3 p, vec3 n) {
    //does good approximations for textures on coordinate planes
    return ((p.xz*n.y) + (p.xy*n.z) + (p.yz*n.x));
}
void main()
{
    vec3 col = texture2D(noise_512, fposition.xy).r * fcolor;
    if (dot(vec3(0., 0., 1.), fnormal) > 0.5) {
        col = texture2D(cat, getTexPos(fposition + 0.5, fnormal)).rgb;
    }
    outputColor = vec4(col, 1.);
}