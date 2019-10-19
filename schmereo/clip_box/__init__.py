from OpenGL import GL
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter


class ClipBox(object):
    def __init__(self):
        self.painter = QPainter()

    def paint_gl(self, gl_widget: "ImageWidget") -> None:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        self.painter.begin(gl_widget)
        self.painter.setRenderHint(QPainter.HighQualityAntialiasing)
        self.painter.setPen(Qt.red)
        self.painter.drawLine(gl_widget.rect().topLeft(), gl_widget.rect().bottomRight())
        self.painter.end()
