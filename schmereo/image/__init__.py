import pkg_resources

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileShader, compileProgram

from schmereo.camera import Camera


class SingleImage(object):
    def __init__(self, camera: Camera):
        self.camera = camera
        self.vao = None
        self.shader = None
        self.texture = None
        self.image = None
        self.image_needs_upload = False
        self.aspect_location = 0
        self.zoom_location = 1
        self.center_location = 2
        self.file_name = None
        self.pixels = None

    def initializeGL(self) -> None:
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(
                pkg_resources.resource_string('schmereo.image', 'image.vert'),
                GL.GL_VERTEX_SHADER),
            compileShader(
                pkg_resources.resource_string('schmereo.image', 'image.frag'),
                GL.GL_FRAGMENT_SHADER),
        )
        self.texture = GL.glGenTextures(1)

    def load_image(self, file_name, image, pixels) -> bool:
        if file_name == self.file_name:
            return True
        self.file_name = file_name
        self.pixels = pixels
        self.image = image
        self.image_needs_upload = True
        return True

    def paintGL(self, aspect_ratio) -> None:
        if self.pixels is None:
            return
        GL.glBindVertexArray(self.vao)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        if self.image_needs_upload:
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
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
            self.image_needs_upload = False
        GL.glUseProgram(self.shader)
        GL.glUniform1f(self.aspect_location, aspect_ratio)
        GL.glUniform1f(self.zoom_location, self.camera.zoom)
        GL.glUniform2fv(self.center_location, 1, self.camera.center.bytes)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
