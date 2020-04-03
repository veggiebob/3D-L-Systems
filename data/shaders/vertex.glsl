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
    fnormal = (modelViewMatrix * vec4(normal, 0.)).xyz;
    gl_Position = projectionMatrix * viewMatrix * modelViewMatrix * vec4(position, 1.);
    fposition = vec3(modelViewMatrix * vec4(position, 1.));
    fcolor = color;
}