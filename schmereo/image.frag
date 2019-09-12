#version 460

uniform sampler2D image;
uniform vec2 image_center = vec2(0.5, 0.5);
uniform float zoom = 1.0;

in noperspective vec2 texCoord;
out vec4 frag_color;

const vec4 bg_color = vec4(vec3(0.2), 1);

void main()
{
    // TODO use 2x2 matrix transformations...
    mat2 scale = mat2(
        zoom, 0,
        0, zoom);

    // correct for image aspect ratio
    ivec2 tsz = textureSize(image, 0);
    float image_aspect = 1;
    if (tsz.y > 0)
        image_aspect = float(tsz.x) / tsz.y;

    vec2 tc = texCoord;
    tc *= zoom;
    vec2 offset = image_center;
    tc += offset;

    vec2 atc = abs(tc);
    float mtc = max(atc.x, atc.y);

    tc *= vec2(1, image_aspect);

    if (mtc > 1)
    {
        // gray background
        frag_color = bg_color;
    }
    else
    {
        // frag_color = vec4(tc, 0.5, 1);
        frag_color = texture(image, tc);
    }
}
