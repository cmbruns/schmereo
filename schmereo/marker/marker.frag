#version 460 core

layout(location=0) uniform sampler2D markerImage;

out vec4 fragColor;

void main()
{
    vec4 color = vec4(1.0, 1.0, 0.2, 0.3);
    fragColor = texture(markerImage, gl_PointCoord) * color;
}
