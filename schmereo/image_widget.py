import pkg_resources

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileShader, compileProgram
from PIL import Image
from PyQt5 import QtGui, QtWidgets


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.vao = None
        self.shader = None
        self.texture = None
        self.image = None
        self.image_needs_upload = False
        self.aspect = 1.0
        self.zoom = 1.0
        self.center = numpy.array((0, 0), dtype=numpy.float32)
        self.aspect_location = 0
        self.zoom_location = 1
        self.center_location = 2
        self.is_dragging = False
        self.previous_mouse = None
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasImage() or md.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                self.image = Image.open(url.toLocalFile())
                self.image_needs_upload = True
                print(self.image)
                self.update()

    def initializeGL(self) -> None:
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(
                pkg_resources.resource_string(__name__, 'image.vert'),
                GL.GL_VERTEX_SHADER),
            compileShader(
                pkg_resources.resource_string(__name__, 'image.frag'),
                GL.GL_FRAGMENT_SHADER),
        )
        self.texture = GL.glGenTextures(1)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if not self.is_dragging:
            return
        if self.previous_mouse is not None:
            dPos = event.pos() - self.previous_mouse
            dx = 2.0 * dPos.x() / self.width()
            dy = -2.0 * dPos.y() / self.width()  # yes, width
            self.center += (-dx, dy)
            self.update()
        self.previous_mouse = event.pos()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.is_dragging = True
        self.previous_mouse = event.pos()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.is_dragging = False
        self.previous_mouse = None

    def wheelEvent(self, event: QtGui.QWheelEvent):
        dScale = event.angleDelta().y() / 120.0
        if dScale == 0:
            return
        dc1 = self.zoom * self.center
        dScale = 1.05 ** -dScale
        self.zoom *= dScale
        dc2 = self.zoom * self.center
        self.center += dc1 - dc2  # TODO: this is wrong
        self.update()

    def paintGL(self) -> None:
        GL.glBindVertexArray(self.vao)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        if self.image_needs_upload:
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGB,
                self.image.width,
                self.image.height,
                0,
                GL.GL_RGB,
                GL.GL_UNSIGNED_BYTE,
                numpy.array(list(self.image.getdata()), dtype=numpy.ubyte),
            )
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
            GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
            self.image_needs_upload = False
        GL.glUseProgram(self.shader)
        GL.glUniform1f(self.aspect_location, self.aspect)
        GL.glUniform1f(self.zoom_location, self.zoom)
        GL.glUniform2fv(self.center_location, 1, self.center)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    def resizeGL(self, width: int, height: int) -> None:
        self.aspect = height/width
