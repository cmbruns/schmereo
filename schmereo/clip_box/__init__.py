import enum
import math

from OpenGL import GL
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QSize, QObject, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath

from schmereo.coord_sys import CanvasPos
from schmereo.camera import Camera
from schmereo.coord_sys import FractionalImagePos, ImagePixelCoordinate


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
    def __init__(self, camera: Camera, images, width=1.0, height=1.0, parent=None):
        super().__init__(parent=parent)
        self.camera = camera
        self.images = images
        self.left = -0.5 * width
        self.right = 0.5 * width
        self.top = -0.5 * height
        self.bottom = 0.5 * height
        self.pen = QPen(QColor(0x40, 0x90, 0xFF, 0x90), 3)
        self.pen.setStyle(Qt.DashLine)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self._is_hovered = False
        self._dirty = False
        self.press_state = None

    def adjust(self, edge: Edge, d_pos: CanvasPos):
        if Edge == Edge.NONE:
            return
        if d_pos.x == d_pos.y == 0:
            return
        self._dirty = True
        if edge & Edge.LEFT:
            self.left += d_pos.x
            self.left = min(self.left, self.right)
        elif edge & Edge.RIGHT:
            self.right += d_pos.x
            self.right = max(self.right, self.left)
        if edge & Edge.TOP:
            self.top += d_pos.y
            self.top = min(self.top, self.bottom)
        elif edge & Edge.BOTTOM:
            self.bottom += d_pos.y
            self.bottom = max(self.bottom, self.top)

    changed = QtCore.pyqtSignal()

    def check_hover(self, pos: CanvasPos, tolerance: float) -> Edge:
        # Make sure we are in the general vicinity
        if pos.x < self.left - tolerance:
            return Edge.NONE
        if pos.x > self.right + tolerance:
            return Edge.NONE
        if pos.y < self.top - tolerance:
            return Edge.NONE
        if pos.y > self.bottom + tolerance:
            return Edge.NONE
        # Vertical
        v_edge = Edge.NONE
        dtop = abs(self.top - pos.y)
        dbottom = abs(self.bottom - pos.y)
        if dtop < dbottom and dtop <= tolerance:
            v_edge = Edge.TOP
        elif dbottom <= tolerance:
            v_edge = Edge.BOTTOM
        else:
            v_edge = Edge.NONE
        # Horizontal
        h_edge = Edge.NONE
        dleft = abs(self.left - pos.x)
        dright = abs(self.right - pos.x)
        if dleft < dright and dleft <= tolerance:
            h_edge = Edge.LEFT
        elif dright <= tolerance:
            h_edge = Edge.RIGHT
        else:
            h_edge = Edge.NONE
        result = h_edge | v_edge
        self.is_hovered = result != Edge.NONE
        return result

    def notify(self):
        if self._dirty:
            self.changed.emit()
        self._dirty = False

    def paint_gl(
        self, window_size: QSize, camera: Camera, painter: QPainter, hover: bool
    ) -> None:
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(self.pen)
        cp = (
            CanvasPos(self.left, self.top),
            CanvasPos(self.right, self.top),
            CanvasPos(self.right, self.bottom),
            CanvasPos(self.left, self.bottom),
        )
        ws = window_size
        scale = 0.5 * camera.zoom * ws.width()
        if hover:
            self.pen.setWidthF(3.0 / scale)
            self.pen.setColor(QColor(0x40, 0xA0, 0xFF, 0x90))
        else:
            self.pen.setWidthF(2.5 / scale)
            self.pen.setColor(QColor(0x40, 0x90, 0xFF, 0x70))
        painter.setPen(self.pen)
        painter.resetTransform()
        painter.translate(0.5 * ws.width(), 0.5 * ws.height())
        painter.translate(-camera.center.x * scale, -camera.center.y * scale)
        painter.scale(scale, scale)
        x, y = cp[0].x, cp[0].y
        w, h = cp[1].x - cp[0].x, cp[3].y - cp[0].y
        rectangle = QtCore.QRectF(x, y, w, h)
        painter.drawRect(rectangle)
        outer_rect = QtCore.QRectF(x - 2, y - 2, w + 4, h + 4)
        # darken everything beyond edge
        outer1 = QPainterPath()
        outer1.addRect(outer_rect)
        outer1.addRect(rectangle)
        if hover:
            painter.fillPath(outer1, QColor(0x20, 0x40, 0x80, 0x50))
        else:
            painter.fillPath(outer1, QColor(0x20, 0x40, 0x80, 0x90))

    def recenter(self):
        center_x = 0.5 * (self.right + self.left)
        center_y = 0.5 * (self.bottom + self.top)
        if center_x == 0 and center_y == 0:
            return
        self._dirty = True
        # 1) change clip box
        self.right -= center_x
        self.left = -self.right
        self.top -= center_y
        self.bottom = -self.top
        # 2) change camera(s)
        dcp = CanvasPos(center_x, center_y)
        self.camera.center -= CanvasPos(center_x, center_y)
        # 3) change image center(s)
        for img in self.images:
            fpc = img.transform.center
            cpc = CanvasPos.from_FractionalImagePos(fpc, img.transform)
            cpc += dcp
            fpc = FractionalImagePos.from_CanvasPos(cpc, img.transform)
            img.transform.center = fpc

    @property
    def size(self) -> ImagePixelCoordinate:
        cp1 = CanvasPos(self.left, self.top)
        cp2 = CanvasPos(self.right, self.bottom)
        xform = self.images[0].transform
        img_size = self.images[0].size()
        fips = [FractionalImagePos.from_CanvasPos(pos, xform) for pos in (cp1, cp2)]
        ipcs = [ImagePixelCoordinate.from_FractionalImagePos(pos, img_size) for pos in fips]
        width = int(round(abs(ipcs[1].x - ipcs[0].x)) + 0.1)
        height = int(round(abs(ipcs[1].y - ipcs[0].y)) + 0.1)
        return ImagePixelCoordinate(width, height)

    @size.setter
    def size(self, value: ImagePixelCoordinate):
        ipc2 = ImagePixelCoordinate(0, 0)
        img_size = self.images[0].size()
        fips = [FractionalImagePos.from_ImagePixelCoordinate(pos, img_size) for pos in (value, ipc2)]
        xform = self.images[0].transform
        cps = [CanvasPos.from_FractionalImagePos(pos, xform) for pos in fips]
        width = abs(cps[1].x - cps[0].x)
        height = abs(cps[1].y - cps[0].y)
        self.right = 0.5 * width
        self.left = -self.right
        self.bottom = 0.5 * height
        self.top = -self.bottom

    @property
    def state(self):
        """Internal state used by AdjustClipBoxCommand"""
        return {
            "left": self.left,
            "right": self.right,
            "top": self.top,
            "bottom": self.bottom,
            "camera_center": (self.camera.center.x, self.camera.center.y),
            "transforms": [i.transform.center[:] for i in self.images],
        }

    @state.setter
    def state(self, data):
        self.left = data["left"]
        self.right = data["right"]
        self.top = data["top"]
        self.bottom = data["bottom"]
        self.camera.center = CanvasPos(*data["camera_center"])
        for i, img in enumerate(self.images):
            img.transform.center = FractionalImagePos(*data["transforms"][i])

    def to_dict(self):
        w, h = self.size
        return {"width": int(w), "height": int(h)}

    def from_dict(self, data):
        if "left" in data:
            self.left = data["left"]
            self.right = data["right"]
            self.top = data["top"]
            self.bottom = data["bottom"]
        else:
            w, h = data["width"], data["height"]
            self.size = ImagePixelCoordinate(w, h)
        print(self.size)
