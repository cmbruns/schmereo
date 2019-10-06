#version 460 core

in vec2 position;  // in image pixels

layout(location=1) uniform ivec2 imageSize = ivec2(640, 480);  // in image pixels
layout(location=2) uniform vec2 transformCenter = vec2(0.0, 0.0);  // in fip? TODO:
layout(location=3) uniform vec2 cameraCenter = vec2(0.0, 0.0);  // in canvas
layout(location=4) uniform float cameraZoom = 1.0;
layout(location=5) uniform float windowAspect = 1.0;
layout(location=6) uniform float transformRotation = 0.0;

void main()
{
    // Keep these transformation in sync with methods in schmereo.coord_sys

    // convert image pixel coordinate to fractional image position
    float imageAspect = imageSize.y / float(imageSize.x);
    vec2 fip = 2.0 * position / vec2(imageSize.xx);
    fip -= vec2(1, imageAspect);

    // convert fractional image position to canvas position
    vec2 cp = fip - transformCenter;  // TODO: scale
    float cr = cos(transformRotation);
    float sr = sin(transformRotation);
    mat2 rot = mat2( cr, sr,
                    -sr, cr);
    cp = rot * cp;


    // convert canvas position to ndc
    vec2 ndc = cp - cameraCenter;
    ndc *= cameraZoom;
    ndc.y *= -1.0 / windowAspect;

    gl_Position = vec4(ndc, 0.5, 1);
    gl_PointSize = 32;
}
