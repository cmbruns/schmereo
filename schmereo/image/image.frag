#version 460

const float PI = 3.1415926535897932384626433832795;

uniform sampler2D image;
layout(location = 3) uniform vec2 image_center = vec2(0);
layout(location = 4) uniform float rotation = 0.0 * PI / 180.0;  // radians

in noperspective vec2 canvasCoord;
out vec4 frag_color;

const vec4 bg_color = vec4(vec3(0.2), 1);

void main()
{
    // correct for image aspect ratio
    ivec2 tsz = textureSize(image, 0);
    float image_aspect = 1;
    if (tsz.x > 0)
        image_aspect = float(tsz.y) / tsz.x;

    float cr = cos(rotation);
    float sr = sin(rotation);
    mat2 rot = mat2(cr, -sr,
                    sr,  cr);
    vec2 fip = rot * canvasCoord;
    fip += image_center;
    vec2 ipc = fip + vec2(1, image_aspect);
    ipc.x *= 0.5;
    ipc.y *= 0.5/image_aspect;

    vec2 rel = ipc - vec2(0.5);
    rel *= 2.0;
    float mtc = max(abs(rel.x), abs(rel.y));

    if (mtc >= 1.0)
    {
        // gray background
        frag_color = bg_color;
    }
    else
    {
        // frag_color = vec4(texCoord, 0.5, 1);
        frag_color = texture(image, ipc);
    }
}
