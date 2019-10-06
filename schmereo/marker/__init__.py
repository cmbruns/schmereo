import pkg_resources
from typing import List

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image

from schmereo.coord_sys import ImagePixelCoordinate


class MarkerSet(object):
    def __init__(self, camera):
        self.camera = camera
        self.vao = None
        self.shader = None
        stream = pkg_resources.resource_stream(__name__, "crosshair64.png")
        self.image = Image.open(stream)
        self.pixels = numpy.frombuffer(
            buffer=self.image.convert("RGBA").tobytes(), dtype=numpy.ubyte
        )
        self.texture = None
        self.points = list()
        self._array = None
        self._dirty_array = False
        self.vbo = None

    def __getitem__(self, index):
        return self.points[index]

    def __len__(self) -> int:
        return len(self.points)

    def __delitem__(self, key):
        del self.points[key]
        self._dirty_array = True

    def add_marker(self, pos: ImagePixelCoordinate):
        self.points.append([*pos])
        self._dirty_array = True

    def add_markers(self, markers: List[ImagePixelCoordinate]):
        for m in markers:
            self.points.append([*m])
        self._dirty_array = True

    def clear(self):
        if len(self.points) == 0:
            return
        self.points[:] = []
        self._dirty_array = True

    def initializeGL(self):
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(
                pkg_resources.resource_string("schmereo.marker", "marker.vert"),
                GL.GL_VERTEX_SHADER,
            ),
            compileShader(
                pkg_resources.resource_string("schmereo.marker", "marker.frag"),
                GL.GL_FRAGMENT_SHADER,
            ),
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
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, False, 0, None)

    def paintGL(self, image_size, transform, camera, window_aspect):
        if not self._dirty_array and self._array is None:
            return
        GL.glBindVertexArray(self.vao)
        if self._dirty_array:
            self._array = numpy.array(self.points, dtype=numpy.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, self._array, GL.GL_STATIC_DRAW)
            self._dirty_array = False
        GL.glUseProgram(self.shader)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glUniform1i(0, 0)  # marker image is in texture unit zero
        GL.glUniform2i(1, *image_size)
        GL.glUniform2f(2, *transform.center)
        GL.glUniform2f(3, *camera.center)
        GL.glUniform1f(4, camera.zoom)
        GL.glUniform1f(5, window_aspect)
        GL.glUniform1f(6, transform.rotation)
        GL.glDrawArrays(GL.GL_POINTS, 0, len(self.points))

    def to_dict(self):
        return [{'x': float(p[0]), 'y': float(p[1])} for p in self.points]

    def from_dict(self, data):
        self.clear()
        for p in data:
            self.add_marker(ImagePixelCoordinate(p['x'], p['y']))
