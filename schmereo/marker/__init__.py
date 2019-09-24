import inspect
import pkg_resources

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image

from schmereo.coord_sys import ImagePixelCoordinate


class Marker(object):
    def __init__(self, pos: ImagePixelCoordinate):
        self.pos = pos
        self.is_manually_placed = False


class MarkerPair(object):
    def __init__(self, left: Marker, right: Marker):
        self.left = left
        self.right = right


class MarkerSet(object):
    def __init__(self, camera):
        self.camera = camera
        self.vao = None
        self.shader = None
        stream = pkg_resources.resource_stream(__name__, 'crosshair64.png')
        self.image = Image.open(stream)
        self.pixels = numpy.frombuffer(buffer=self.image.convert('RGBA').tobytes(), dtype=numpy.ubyte)
        self.texture = None

    def initializeGL(self):
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(
                pkg_resources.resource_string('schmereo.marker', 'marker.vert'),
                GL.GL_VERTEX_SHADER),
            compileShader(
                pkg_resources.resource_string('schmereo.marker', 'marker.frag'),
                GL.GL_FRAGMENT_SHADER),
        )
        GL.glBindVertexArray(self.vao)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            self.image.width,
            self.image.height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            self.pixels,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)

    def paintGL(self, image_size, transform, camera, window_aspect):
        GL.glBindVertexArray(self.vao)
        GL.glUseProgram(self.shader)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glUniform1i(0, 0)  # marker image is in texture unit zero
        GL.glUniform2i(1, *image_size)
        GL.glUniform2f(2, *transform.center)
        GL.glUniform2f(3, *camera.center)
        GL.glUniform1f(4, camera.zoom)
        GL.glUniform1f(5, window_aspect)
        GL.glDrawArrays(GL.GL_POINTS, 0, 1)
