#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 color;

varying vec3 fposition;
varying vec3 fnormal;
varying vec3 fcolor;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

void main()
{
//    fnormal = (projectionMatrix * vec4(normal, 1.)).xyz;
    fnormal = normal;
//    look = (projectionMatrix * viewMatrix * vec4(0., 0., 1., 1.)).xyz;
//    look = vec3(0., 0., 1.);
    gl_Position = projectionMatrix * viewMatrix * modelViewMatrix * vec4(position, 1.);
    fposition = gl_Position.xyz;
    fcolor = color;
}