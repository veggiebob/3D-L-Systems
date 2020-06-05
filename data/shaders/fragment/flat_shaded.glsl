#version 330
#define useVertexColor
#define unlit

out vec4 outputColor;

in vec4 cameraPosition;
in vec3 fnormal;
in vec3 fcolor;
in vec3 fposition;
in float planeDistance;

uniform vec4 baseColor;//mat

//globals
uniform vec3 light_pos;
uniform float time;

const vec3 ambient = vec3(0.2);

const vec3 look = vec3(0., 0., 1.);
const vec3 light_col = vec3(1.);
const float light_strength = 1.0;
float alpha_depth_func (float x) {
//    return min(1., 1.4 * pow(max(d,0.), 1./6.));
    return 1. + min(x-0.2, 0.0) * 5.;
}
void main()
{
    //FresnelSchlick(h,v,F0)=F0+(1−F0)(1−(h⋅v))^5
    //F0 = base reflectivity
    //h = h=l+v/∥l+v∥
    //l = surface-to-light vector
    //v = surface-to-camera vector
    if (planeDistance < 0) discard;
    #ifdef useVertexColor
    vec4 t = vec4(fcolor, 1.);
    #else
    vec4 t = vec4(baseColor);
    #endif
    vec3 col = t.rgb;
#ifndef unlit
    col *= ambient;
    vec3 normal = normalize(fnormal);
    float diffuse_weight, specular_weight;
    diffuse_weight = 0.4;
    specular_weight = 0.6;
    vec3 light_dir = normalize(light_pos - fposition);
    float diffuse = max(dot(light_dir, normal), 0.);
    float specular = pow(max(dot(look, -reflect(normal, light_dir)), 0.), 16.);
    col += (diffuse * diffuse_weight + specular * specular_weight) * light_col * light_strength;
#endif
    outputColor = vec4(col, 1.0);//alpha_depth_func(cameraPosition.z));
}