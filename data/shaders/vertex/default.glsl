#version 330
#define skybox
// GLTF: COLOR_0,JOINTS_0,NORMAL,POSITION,TANGENT,TEXCOORD_0,TEXCOORD_1,WEIGHTS_0
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 color_0;
layout(location = 3) in vec2 texcoord_0;
layout(location = 4) in vec2 texcoord_1;
layout(location = 5) in vec3 tangent; // hm
layout(location = 6) in vec3 joints_0; // hm
layout(location = 7) in vec3 weights_0; // hm
//*hm: don't know if those are the right types

out vec3 fposition;
out vec3 fnormal;
out vec3 fcolor;
out vec2 texCoord;
out vec2 texCoord2;
out vec4 cameraPosition;
out float planeDistance;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

uniform float time;

////<x,y,z,w> = <a,b,c,d> where the plane is defined by ax + by + cz + d = 0
////this means that <a,b,c> is the normal of the plane
uniform vec4 plane;
uniform bool hasPlane;
mat4 no_translate (mat4 mat) {
    mat[3].xyz = vec3(0.);
    return mat;
}
const float stupid_scale = 10000.;
void main()
{
    #ifndef skybox
    fnormal = (modelViewMatrix * vec4(normal, 0.)).xyz;
    fposition = vec3(modelViewMatrix * vec4(position, 1.));
    gl_Position = projectionMatrix * viewMatrix * modelViewMatrix * vec4(position, 1.);
    #else
    fnormal = normal;
    fposition = position*stupid_scale;
    gl_Position = (projectionMatrix) * no_translate(viewMatrix) * vec4(position*stupid_scale, 1.);
    #endif
    cameraPosition = gl_Position;
    fcolor = color_0;
    texCoord = texcoord_0;
    texCoord2 = texcoord_1;
    if (hasPlane)
    planeDistance = dot(plane.xyz, fposition) + plane.w;
    else planeDistance = 1.0; // everything visible
}