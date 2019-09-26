from functools import partial
from typing import Optional

import numpy
from PyQt5 import QtCore, QtGui, QtWidgets

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
        self.is_dragging = False
        self.previous_mouse: Optional[WindowPos] = None
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    def add_marker(self, action):
        mouse_pos = action.data()
        image_pos = self.image_from_window(mouse_pos)
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

    def image_from_window(self, q_point: QtCore.QPoint) -> ImagePixelCoordinate:
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
            ip = self.image_from_window(event.pos())
            self.messageSent.emit(f'Pixel: {ip.x: 0.1f}, {ip.y: 0.1f}', 1500)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.is_dragging = True
        self.previous_mouse = WindowPos.from_QPoint(event.pos())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.is_dragging = False
        self.previous_mouse = None

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
