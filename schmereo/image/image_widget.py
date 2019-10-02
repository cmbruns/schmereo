import datetime
from functools import partial
from typing import Optional

import numpy
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from schmereo.camera import Camera
from schmereo.coord_sys import FractionalImagePos, WindowPos, CanvasPos, ImagePixelCoordinate
from schmereo.image.single_image import SingleImage
from schmereo.marker import MarkerSet


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, camera=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        if camera is None:
            camera = Camera()
        self.image = SingleImage(camera=camera)
        self.markers = MarkerSet(camera=camera)
        self.aspect_ratio = 1.0
        # TODO: drag detection object
        self.is_dragging = False
        self.previous_mouse: Optional[WindowPos] = None
        #
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        # TODO: cursor manager object
        self.openhand_cursor = QtGui.QCursor(QtGui.QPixmap('cursor-openhand.png'))
        self.grab_cursor = QtGui.QCursor(QtGui.QPixmap('cursor-closedhand.png'))
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

    def add_marker(self, action):
        mouse_pos = action.data()
        image_pos = self.image_from_window_qpoint(mouse_pos)
        self.markers.add_marker([*image_pos])
        self.update()

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
        add_marker_action = QtWidgets.QAction(text='Add Marker Here', parent=self)
        add_marker_action.setData(mouse_pos)
        add_marker_action.triggered.connect(partial(self.add_marker, add_marker_action))
        menu = QtWidgets.QMenu(self)
        menu.addAction(add_marker_action)
        menu.addAction(QtWidgets.QAction(text='Cancel [ESC]', parent=self))
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
        c_args = (self.camera, self.size())
        cp = CanvasPos.from_WindowPos(wp, *c_args)
        return self.image_from_canvas(cp)

    def initializeGL(self) -> None:
        super().initializeGL()
        self.image.initializeGL()
        self.markers.initializeGL()

    def load_image(self, file_name, image, pixels) -> bool:
        return self.image.load_image(file_name, image, pixels)

    messageSent = QtCore.pyqtSignal(str, int)

    def mouseClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self.maybe_clicking = False
        if self._add_marker_mode:
            image_pos = self.image_from_window_qpoint(event.pos())
            self.markers.add_marker([*image_pos])
            self.update()
            self.set_add_marker_mode(False)

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.maybe_clicking = False

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_dragging:
            wp = WindowPos.from_QPoint(event.pos())
            c_args = (self.camera, self.size())
            cp = CanvasPos.from_WindowPos(wp, *c_args)
            if self.previous_mouse is not None:
                dPosC = cp - CanvasPos.from_WindowPos(self.previous_mouse, *c_args)
                self.camera.center -= dPosC
                self.camera.notify()  # update UI now
            self.previous_mouse = wp
        else:
            ip = self.image_from_window_qpoint(event.pos())
            self.messageSent.emit(f'Pixel: {ip.x: 0.1f}, {ip.y: 0.1f}', 3000)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # drag detection
        self.is_dragging = True
        self.previous_mouse = WindowPos.from_QPoint(event.pos())
        # click detection
        self.maybe_clicking = True
        self.mouse_press_pos = QtCore.QPoint(event.pos().x(), event.pos().y())
        self.mouse_press_time = datetime.datetime.now()
        # cursor shape
        if self.drag_cursor != self.hover_cursor:
            self.setCursor(self.drag_cursor)
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        # drag detection
        self.is_dragging = False
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
        # cursor shape
        if self.drag_cursor != self.hover_cursor:
            self.setCursor(self.hover_cursor)
            self.update()

    def set_add_marker_mode(self, checked: bool = True):
        if checked:
            self.hover_cursor = Qt.CrossCursor
            self.drag_cursor = Qt.CrossCursor
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
            self.camera.center += (mpc1 - mpc2)
        else:
            # zoom centered on widget center
            self.camera.zoom *= dScale
        self.camera.notify()

    def paintGL(self) -> None:
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

    def resizeGL(self, width: int, height: int) -> None:
        self.aspect_ratio = height/width
