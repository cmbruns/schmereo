import datetime
import enum
from functools import partial
import pkg_resources
from typing import Optional

import numpy
from OpenGL import GL
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from schmereo.camera import Camera
from schmereo.clip_box import ClipBox, Edge
from schmereo.command import AddMarkerCommand
from schmereo.coord_sys import (
    FractionalImagePos,
    WindowPos,
    CanvasPos,
    ImagePixelCoordinate,
)
from schmereo.image.single_image import SingleImage
from schmereo.marker import MarkerSet


def _make_cursor(file_name):
    fh = pkg_resources.resource_stream("schmereo", file_name)
    img = ImageQt(Image.open(fh).convert("RGBA"))
    cursor = QtGui.QCursor(QtGui.QPixmap.fromImage(img))
    return cursor


class DragMode(enum.Enum):
    NONE = 1
    PAN = 2
    CLIP_BOX = 3
    MARKER = 4  # TODO:


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, camera: Camera = None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        if camera is None:
            camera = Camera()
        self.image = SingleImage(camera=camera)
        self.markers = MarkerSet(camera=camera)
        self.aspect_ratio = 1.0
        # TODO: drag detection object
        self.drag_mode = DragMode.NONE
        self.latent_drag_mode = DragMode.PAN
        self.clip_box_edge = Edge.NONE
        self.previous_mouse: Optional[WindowPos] = None
        #
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        # TODO: cursor manager object
        self.openhand_cursor = _make_cursor("cursor-openhand20.png")
        self.grab_cursor = _make_cursor("cursor-closedhand20.png")
        self.cross_cursor = _make_cursor("crosshair32.png")
        self.drag_cursor = self.grab_cursor
        self.hover_cursor = self.openhand_cursor
        self.setCursor(self.hover_cursor)
        # TODO: click detection object
        self.mouse_press_pos = None
        self.mouse_press_time = datetime.datetime.now()
        self.maybe_clicking = False
        #
        self._add_marker_mode = False
        #
        self.image.messageSent.connect(self.messageSent)
        self.undo_stack = None
        #
        self.clip_box = None
        self.clip_box_is_hovered = False
        self.painter = QtGui.QPainter()

    def add_marker(self, image_pos: ImagePixelCoordinate):
        self.markers.add_marker(image_pos)
        self.marker_added.emit()
        self.update()

    def add_marker_from_action(self, action):
        mouse_pos = action.data()
        image_pos = self.image_from_window_qpoint(mouse_pos)
        self.undo_stack.push(AddMarkerCommand(self, image_pos))

    @property
    def camera(self):
        return self.image.camera

    @camera.setter
    def camera(self, value):
        self.image.camera = value
        self.image.camera.changed.connect(self.update)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if self.image.image is None:
            return
        mouse_pos = event.pos()
        add_marker_action = QtWidgets.QAction(text="Add Marker Here", parent=self)
        add_marker_action.setData(mouse_pos)
        add_marker_action.triggered.connect(
            partial(self.add_marker_from_action, add_marker_action)
        )
        menu = QtWidgets.QMenu(self)
        menu.addAction(add_marker_action)
        menu.addAction(QtWidgets.QAction(text="Cancel [ESC]", parent=self))
        menu.exec(event.globalPos())

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasImage() or md.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                self.file_dropped.emit(url.toLocalFile())

    file_dropped = QtCore.pyqtSignal(str)

    def fract_from_image(self, pos: ImagePixelCoordinate) -> FractionalImagePos:
        img = self.image.image
        img_size = (1, 1)
        if img:
            img_size = (img.width, img.height)
        return FractionalImagePos.from_ImagePixelCoordinate(pos, img_size)

    def image_from_canvas(self, pos: CanvasPos) -> ImagePixelCoordinate:
        fip = FractionalImagePos.from_CanvasPos(pos, self.image.transform)
        img = self.image.image
        img_size = (1, 1)
        if img:
            img_size = (img.width, img.height)
        ip = ImagePixelCoordinate.from_FractionalImagePos(fip, img_size)
        return ip

    def image_from_window_qpoint(self, q_point: QtCore.QPoint) -> ImagePixelCoordinate:
        wp = WindowPos.from_QPoint(q_point)
        cp = CanvasPos.from_WindowPos(wp, self.camera, self.size())
        return self.image_from_canvas(cp)

    def initializeGL(self) -> None:
        super().initializeGL()
        self.image.initializeGL()
        self.markers.initializeGL()

    def load_image(self, file_name) -> bool:
        result = self.image.load_image(file_name)
        return result

    marker_added = QtCore.pyqtSignal()

    messageSent = QtCore.pyqtSignal(str, int)

    def mouseClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self.maybe_clicking = False
        if self._add_marker_mode and (event.button() == Qt.LeftButton):
            image_pos = self.image_from_window_qpoint(event.pos())
            self.undo_stack.push(AddMarkerCommand(self, image_pos))

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.maybe_clicking = False

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.drag_mode != DragMode.NONE and not event.buttons() & Qt.LeftButton:
            return
        wp = WindowPos.from_QPoint(event.pos())
        if self.drag_mode != DragMode.NONE and self.previous_mouse is None:
            self.previous_mouse = wp
            return
        cp = CanvasPos.from_WindowPos(wp, self.camera, self.size())
        if self.drag_mode != DragMode.NONE:
            dPosC = cp - CanvasPos.from_WindowPos(
                self.previous_mouse, self.camera, self.size()
            )
            self.previous_mouse = wp
            # TODO: marker drage takes top priority
            # TODO: clip box drag takes second priority
            if self.drag_mode == DragMode.CLIP_BOX:
                self.clip_box.adjust(self.clip_box_edge, dPosC)
                self.clip_box.notify()
            elif self.drag_mode == DragMode.PAN:
                self.camera.center -= dPosC
                self.camera.notify()  # update UI now
        else:  # just hovering, not dragging
            self.clip_box_edge = self.clip_box.check_hover(
                cp, tolerance=20.0 / (self.size().width() * self.camera.zoom)
            )
            if self.clip_box_edge == Edge.NONE:
                is_hovered = False
                self.setCursor(self.hover_cursor)
                self.latent_drag_mode = DragMode.PAN
            else:
                is_hovered = True
                self.latent_drag_mode = DragMode.CLIP_BOX
                if self.clip_box_edge in (Edge.TOP, Edge.BOTTOM):
                    self.setCursor(Qt.SizeVerCursor)
                elif self.clip_box_edge in (Edge.LEFT, Edge.RIGHT):
                    self.setCursor(Qt.SizeHorCursor)
                elif self.clip_box_edge in (Edge.TOP_LEFT, Edge.BOTTOM_RIGHT):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif self.clip_box_edge in (Edge.TOP_RIGHT, Edge.BOTTOM_LEFT):
                    self.setCursor(Qt.SizeBDiagCursor)
            if self.clip_box_is_hovered != is_hovered:
                self.clip_box_is_hovered = is_hovered
                self.update()
            #
            ip = self.image_from_window_qpoint(event.pos())
            self.messageSent.emit(f"Pixel: {ip.x: 0.1f}, {ip.y: 0.1f}", 3000)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if not event.buttons() & Qt.LeftButton:
            return
        # drag detection
        self.drag_mode = self.latent_drag_mode
        wp = WindowPos.from_QPoint(event.pos())
        self.previous_mouse = wp
        # click detection
        self.maybe_clicking = True
        self.mouse_press_pos = QtCore.QPoint(event.pos().x(), event.pos().y())
        self.mouse_press_time = datetime.datetime.now()
        # cursor shape
        if self.drag_cursor != self.hover_cursor:
            self.setCursor(self.drag_cursor)
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        # cursor shape
        if self.drag_cursor != self.hover_cursor:
            self.setCursor(self.hover_cursor)
        # drag detection
        self.drag_mode = DragMode.NONE
        self.previous_mouse = None
        # click detection
        d2 = 1000
        if self.mouse_press_pos:
            dp = event.pos() - self.mouse_press_pos
            d2 = QtCore.QPoint.dotProduct(dp, dp)  # squared distance in pixels
        if d2 > 10:  # TODO: calibrate
            self.maybe_clicking = False  # too far
        dt = datetime.datetime.now() - self.mouse_press_time
        ms = dt.total_seconds() * 1000.0  # milliseconds
        if ms > 800:
            self.maybe_clicking = False
        if ms <= 0:
            self.maybe_clicking = False
        if self.maybe_clicking:
            self.mouseClickEvent(event)
        self.maybe_clicking = False
        self.mouse_press_pos = None

    def set_add_marker_mode(self, checked: bool = True):
        if checked:
            self.hover_cursor = self.cross_cursor
            self.drag_cursor = self.grab_cursor
        else:
            self.hover_cursor = self.openhand_cursor
            self.drag_cursor = self.grab_cursor
        self._add_marker_mode = checked
        self.setCursor(self.hover_cursor)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        dScale = event.angleDelta().y() / 120.0
        if dScale == 0:
            return
        dScale = 1.10 ** dScale
        # Keep location under mouse during zoom
        bKeepLocation = True
        if bKeepLocation:
            # zoom centered on current mouse pointer location
            mouse_pos = WindowPos.from_QPoint(event.pos())
            c_args = (self.camera, self.size())
            mpc1 = CanvasPos.from_WindowPos(mouse_pos, *c_args)
            self.camera.zoom *= dScale
            mpc2 = CanvasPos.from_WindowPos(mouse_pos, *c_args)
            self.camera.center += mpc1 - mpc2
        else:
            # zoom centered on widget center
            self.camera.zoom *= dScale
        self.camera.notify()

    def paintGL(self) -> None:
        self.painter.beginNativePainting()
        self.image.paintGL(self.aspect_ratio)
        img = self.image.image
        if img:
            image_size = numpy.array([img.width, img.height], dtype=numpy.int32)
        else:
            image_size = numpy.array([640, 480], dtype=numpy.int32)
        self.markers.paintGL(
            image_size=image_size,
            transform=self.image.transform,
            camera=self.camera,
            window_aspect=self.aspect_ratio,
        )
        self.painter.endNativePainting()
        if img:
            assert self.painter.begin(self)
            self.clip_box.paint_gl(
                window_size=self.size(),
                camera=self.camera,
                painter=self.painter,
                hover=self.clip_box_is_hovered,
            )
            self.painter.end()

    def resizeGL(self, width: int, height: int) -> None:
        self.aspect_ratio = height / width

    def to_dict(self):
        return {"image": self.image.to_dict(), "markers": self.markers.to_dict()}

    def from_dict(self, data):
        self.image.from_dict(data["image"])
        self.markers.from_dict(data["markers"])

    def x_fract_from_canvas(self, pos: CanvasPos) -> FractionalImagePos:
        return FractionalImagePos.from_CanvasPos(pos, self.image.transform)

    def x_canvas_from_image(self, pos: ImagePixelCoordinate) -> CanvasPos:
        f = self.fract_from_image(pos)
        xform = self.image.transform
        c = CanvasPos.from_FractionalImagePos(f, xform)
        return c
