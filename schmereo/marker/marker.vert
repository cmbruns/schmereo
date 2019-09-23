#version 460 core

layout(location=1) uniform sampler2D parentImage;

const vec2 testPosition = vec2(0, 0);  // image pixels

void main()
{
    ivec2 imageSize = textureSize(parentImage, 0);

    gl_Position = vec4(testPosition, 0.5, 1);
    gl_PointSize = 48;
}
