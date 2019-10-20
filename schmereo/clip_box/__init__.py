import enum

from OpenGL import GL
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, QObject
from PyQt5.QtGui import QPainter, QPen, QColor

from schmereo import CanvasPos
from schmereo.camera import Camera


class Edge(enum.IntFlag):
    #        HH_VV
    NONE = 0b00_00
    TOP = 0b00_01
    BOTTOM = 0b00_10
    LEFT = 0b01_00
    RIGHT = 0b10_00
    TOP_RIGHT = TOP | RIGHT
    BOTTOM_RIGHT = BOTTOM | RIGHT
    BOTTOM_LEFT = BOTTOM | LEFT
    TOP_LEFT = TOP | LEFT


class ClipBox(QObject):
    def __init__(self, width=1.0, height=1.0, parent=None):
        super().__init__(parent=parent)
        self.width = width  # in Canvas coordinates
        self.height = height
        self.pen = QPen(QColor(0x40, 0x80, 0xFF, 0x90), 3)
        self.pen.setStyle(Qt.DashLine)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self._is_hovered = False

    def check_hover(self, pos: CanvasPos, tolerance: float) -> Edge:
        # Vertical
        v_edge = Edge.NONE
        dtop = abs(-self.height / 2.0 - pos.y)
        dbottom = abs(self.height / 2.0 - pos.y)
        if dtop < dbottom and dtop <= tolerance:
            v_edge = Edge.TOP
        elif dbottom <= tolerance:
            v_edge = Edge.BOTTOM
        else:
            v_edge = Edge.NONE
        # Horizontal
        h_edge = Edge.NONE
        dleft = abs(-self.width / 2.0 - pos.x)
        dright = abs(self.width / 2.0 - pos.x)
        if dleft < dright and dleft <= tolerance:
            h_edge = Edge.LEFT
        elif dright <= tolerance:
            h_edge = Edge.RIGHT
        else:
            h_edge = Edge.NONE
        result = h_edge | v_edge
        self.is_hovered = result != Edge.NONE
        return result

    @property
    def is_hovered(self) -> bool:
        return self._is_hovered

    @is_hovered.setter
    def is_hovered(self, value: bool):
        if value == self._is_hovered:
            return
        self._is_hovered = value

    def paint_gl(self, window_size: QSize, camera: Camera, painter: QPainter) -> None:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(self.pen)
        w, h = self.width / 2.0, self.height / 2.0
        cp = (CanvasPos(-w, -h), CanvasPos(w, -h), CanvasPos(w, h), CanvasPos(-w, h))
        ws = window_size
        scale = 0.5 * camera.zoom * ws.width()
        self.pen.setWidthF(3.0 / scale)
        painter.setPen(self.pen)
        painter.resetTransform()
        painter.translate(0.5 * ws.width(), 0.5 * ws.height())
        painter.translate(-camera.center.x * scale, -camera.center.y * scale)
        painter.scale(scale, scale)
        rectangle2 = QtCore.QRectF(
            cp[0].x, cp[0].y, cp[1].x - cp[0].x, cp[3].y - cp[0].y
        )
        painter.drawRect(rectangle2)
