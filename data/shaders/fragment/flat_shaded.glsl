#version 330
//#define clippingPlane

out vec4 outputColor;

in vec4 cameraPosition;
in vec3 fnormal;
in vec3 fcolor;
in vec3 fposition;
//#ifdef clippingPlane
//in float planeDistance;
//#endif

uniform vec3 baseColor;//mat

//globals
uniform vec3 light_pos;
uniform float time;

const vec3 ambient = vec3(0.7);

const vec3 look = vec3(0., 0., 1.);
const vec3 light_col = vec3(1.);
const float light_strength = 1.0;

//rotate vector
vec3 qrot(vec4 q, vec3 v) {
    return v + 2.0*cross(q.xyz, cross(q.xyz,v) + q.w*v);
}

vec4 quat_rotation (vec3 direction, float w) {
    return vec4(normalize(direction)*(1.-w*w), w);
}
vec3 map_direction (vec3 normal, vec3 p_normal, vec3 new_normal) {
    normal = normalize(normal);
    p_normal = normalize(p_normal);
    new_normal = normalize(new_normal);
    vec3 dir = cross(normal, new_normal);
    float theta = acos(dot(normal, new_normal));
    float w = cos(theta/2.);
    vec4 quat = normalize(vec4(dir * sin(theta/2.), w));
    return qrot(quat, p_normal);
}
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
//    #ifdef clippingPlane
//    if (planeDistance < 0) discard; // discard pixel if it's on the wrong side
//    #endif
    vec4 t = vec4(fcolor, 1.);
    vec3 col = t.rgb * ambient * baseColor;
    vec3 normal = normalize(fnormal);
    float diffuse_weight, specular_weight;
    diffuse_weight = 0.4;
    specular_weight = 0.6;
    vec3 light_dir = normalize(light_pos - fposition);
    float diffuse = max(dot(light_dir, normal), 0.);
    float specular = pow(max(dot(look, -reflect(normal, light_dir)), 0.), 16.);
    col += (diffuse * diffuse_weight + specular * specular_weight) * light_col * light_strength;
    outputColor = vec4(col, 1.0);//alpha_depth_func(cameraPosition.z));
}