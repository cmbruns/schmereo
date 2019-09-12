#version 460

layout(location = 0) uniform float windowAspect = 1.0;

const float s = 0.9;
const vec4 SCREEN_QUAD[4] = vec4[4](
    vec4( s, -s, 0.5, 1),
    vec4( s,  s, 0.5, 1),
    vec4(-s, -s, 0.5, 1),
    vec4(-s,  s, 0.5, 1)
);
const float t = 1.0;
const vec2 CANVAS_COORD[4] = vec2[4](
    vec2( t,  t),
    vec2( t, -t),
    vec2(-t,  t),
    vec2(-t, -t)
);

// output coordinate system is the CANVAS frame
// 1 unit = 1/2 the width of the left image
// origin = center of screen
// home position:
//   center of image is at origin
//   origin is at center of screen
out noperspective vec2 canvasCoord;

void main() {
    gl_Position = SCREEN_QUAD[gl_VertexID];
    canvasCoord = CANVAS_COORD[gl_VertexID] * vec2(1, windowAspect);
}
