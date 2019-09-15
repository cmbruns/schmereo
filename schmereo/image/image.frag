#version 460

uniform sampler2D image;
layout(location = 3) uniform vec2 image_center = vec2(0);

in noperspective vec2 canvasCoord;
out vec4 frag_color;

const vec4 bg_color = vec4(vec3(0.2), 1);

void main()
{
    // correct for image aspect ratio
    ivec2 tsz = textureSize(image, 0);
    float image_aspect = 1;
    if (tsz.y > 0)
        image_aspect = float(tsz.x) / tsz.y;

    vec2 imgCoord = canvasCoord;
    imgCoord.y *= image_aspect;

    imgCoord += image_center;

    vec2 texCoord = 0.5 * (imgCoord + vec2(1));

    float mtc = max(abs(imgCoord.x), abs(imgCoord.y));

    if (mtc >= 1.0)
    {
        // gray background
        frag_color = bg_color;
    }
    else
    {
        // frag_color = vec4(texCoord, 0.5, 1);
        frag_color = texture(image, texCoord);
    }
}
