#version 330
in vec2 texCoord;
out vec4 outputColor;
uniform sampler2D FBOscreen;//mat
//uniform sampler2D FBOreflection;//mat
uniform float time;
bool less (vec2 a, vec2 b) {
    bvec2 l = lessThan(a, b);
    return l.x && l.y;
}
vec3 imageBox (vec2 point, vec4 box) { // -> (x,y) as uv and z>0 as 'in the box'
    vec2 n = (point - box.xy) / box.zw;
    float in_box = -1.;
    if (less(vec2(0.), n) && less(n, vec2(1.)))
        in_box = 1.;
    return vec3(n, in_box);
}
void main() {
//    vec4 box = vec4(0.02, 0.02, 0.3, 0.3);
//    vec3 corner_display = imageBox(texCoord, box);
//    vec3 texcolor;
//    if (corner_display.z > 0.) {
//        texcolor = texture2D(FBOreflection, corner_display.xy).rgb;
//    } else {
//        texcolor = texture2D(FBOscreen, texCoord).rgb;
//    }
//    texcolor += (1.+sin(texCoord.x*20.+time)) * vec3(0., 0.2, 0.3) / 2.;
    vec3 texcolor = texture2D(FBOscreen, texCoord).rgb;
    outputColor = vec4(texcolor, 1.);
//    vec4 tex = texture2D(FBOscreen, texCoord);
//    vec3 col = mix(vec3(1.), tex.rgb, 0.9);
//    outputColor = vec4(col, 1.);
}
