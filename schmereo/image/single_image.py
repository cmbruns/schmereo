import pkg_resources

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image
from PyQt5.QtCore import QObject, pyqtSignal

from schmereo.camera import Camera
from schmereo.coord_sys import ImageTransform


class SingleImage(QObject):
    def __init__(self, camera: Camera):
        super().__init__()
        self.camera = camera
        self.vao = None
        self.shader = None
        self.texture = None
        self.image = None
        self.image_needs_upload = False
        self.aspect_location = 0
        self.zoom_location = 1
        self.canvas_center_location = 2
        self.image_center_location = 3
        self.rotation_location = 4
        self.file_name = None
        self.pixels = None
        self.transform = ImageTransform()

    def initializeGL(self) -> None:
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(
                pkg_resources.resource_string("schmereo.image", "image.vert"),
                GL.GL_VERTEX_SHADER,
            ),
            compileShader(
                pkg_resources.resource_string("schmereo.image", "image.frag"),
                GL.GL_FRAGMENT_SHADER,
            ),
        )
        self.texture = GL.glGenTextures(1)

    def load_image(self, file_name) -> bool:
        if file_name == self.file_name:
            return True
        image = Image.open(file_name)
        if image is None:
            self.log_message(f"ERROR: Image load failed.")
            return False
        self.log_message(f"Processing image {file_name}...")
        pixels = numpy.frombuffer(
            buffer=image.convert("RGBA").tobytes(), dtype=numpy.ubyte
        )
        if pixels is None or len(pixels) < 1:
            self.log_message(f"ERROR: Image processing failed.")
            return False
        self.log_message(f"Finished processing image {file_name}")
        self.file_name = file_name
        self.pixels = pixels
        self.image = image
        self.image_needs_upload = True
        return True

    def log_message(self, message):
        self.messageSent.emit(message, 5000)

    messageSent = pyqtSignal(str, int)

    def paintGL(self, aspect_ratio, camera=None) -> None:
        if self.pixels is None:
            return
        if camera is None:
            camera = self.camera
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
            # TODO: implement toggle between NEAREST, LINEAR, CUBIC...
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST
            )
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR
            )
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE
            )
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE
            )
            GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
            self.image_needs_upload = False
        GL.glUseProgram(self.shader)
        GL.glUniform1f(self.aspect_location, aspect_ratio)
        GL.glUniform1f(self.zoom_location, camera.zoom)
        GL.glUniform2fv(self.canvas_center_location, 1, camera.center.bytes)
        GL.glUniform2fv(self.image_center_location, 1, self.transform.center.bytes)
        GL.glUniform1f(self.rotation_location, self.transform.rotation)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    def size(self):
        return self.image.width, self.image.height

    def to_dict(self):
        return {
            'file_name': self.file_name,
            'transform': self.transform.to_dict(self),
        }

    def from_dict(self, data):
        self.load_image(data['file_name'])
        self.transform.from_dict(data['transform'], self)
