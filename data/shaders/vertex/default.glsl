#version 330
//#define clippingPlane
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
//#ifdef clippingPlane
//out float planeDistance;
//#endif

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

uniform float time;

//#ifdef clippingPlane
////<x,y,z,w> = <a,b,c,d> where the plane is defined by ax + by + cz + d = 0
////this means that <a,b,c> is the normal of the plane
//uniform vec4 plane;//mat
//#endif

void main()
{
    fnormal = (modelViewMatrix * vec4(normal, 0.)).xyz;
    fposition = vec3(modelViewMatrix * vec4(position, 1.));
    gl_Position = projectionMatrix * viewMatrix * modelViewMatrix * vec4(position, 1.);
    cameraPosition = gl_Position;
    fcolor = vec3(1.0, 1.0, 1.0);
    texCoord = texcoord_0;
    texCoord2 = texcoord_1;
//    #ifdef clippingPlane
//    planeDistance = dot(plane.xyz, position) + plane.w;
//    #endif
}