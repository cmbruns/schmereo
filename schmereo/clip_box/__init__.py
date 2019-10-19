from OpenGL import GL
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QPen, QColor

from schmereo import CanvasPos
from schmereo.camera import Camera


class ClipBox(object):
    def __init__(self, width=1.0, height=1.0):
        self.width = width  # in Canvas coordinates
        self.height = height
        self.pen = QPen(QColor(0x40, 0x80, 0xFF, 0x90), 3)
        self.pen.setStyle(Qt.DashLine)

    def check_hover(self, pos: CanvasPos):
        pass  # TODO:

    def paint_gl(self, window_size: QSize, camera: Camera, painter: QPainter) -> None:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(self.pen)
        w, h = self.width/2.0, self.height/2.0
        cp = (CanvasPos(-w, -h), CanvasPos(w, -h), CanvasPos(w, h), CanvasPos(-w, h))
        ws = window_size
        scale = 0.5 * camera.zoom * ws.width()
        self.pen.setWidthF(3.0/scale)
        painter.setPen(self.pen)
        painter.resetTransform()
        painter.translate(0.5 * ws.width(), 0.5 * ws.height())
        painter.translate(-camera.center.x * scale, -camera.center.y * scale)
        painter.scale(scale, scale)
        rectangle2 = QtCore.QRectF(cp[0].x, cp[0].y, cp[1].x - cp[0].x, cp[3].y - cp[0].y)
        painter.drawRect(rectangle2)
