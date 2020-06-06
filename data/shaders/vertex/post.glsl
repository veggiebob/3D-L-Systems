#version 330
in vec3 position;
in vec2 texcoord_0;
out vec2 texCoord;
void main() {
    vec3 pos = (position*2)-1;
    texCoord = texcoord_0;
    gl_Position = vec4(pos, 1.);
}
