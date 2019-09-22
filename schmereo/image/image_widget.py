from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from schmereo.camera import Camera
from schmereo.coord_sys import FractionalImagePos, WindowPos, CanvasPos
from schmereo.image.single_image import SingleImage
from schmereo.image.action import AddMarkerAction
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
        mouse_pos = WindowPos.from_QPoint(event.pos())
        menu = QtWidgets.QMenu(self)
        menu.addAction(AddMarkerAction(parent=self, mouse_pos=mouse_pos))
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

    def initializeGL(self) -> None:
        super().initializeGL()
        self.image.initializeGL()
        self.markers.initializeGL()

    def load_image(self, file_name, image, pixels) -> bool:
        return self.image.load_image(file_name, image, pixels)

    messageSent = QtCore.pyqtSignal(str, int)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        wp = WindowPos.from_QPoint(event.pos())
        c_args = (self.camera, self.size())
        cp = CanvasPos.from_WindowPos(wp, *c_args)
        if self.is_dragging:
            if self.previous_mouse is not None:
                dPosC = cp - CanvasPos.from_WindowPos(self.previous_mouse, *c_args)
                self.camera.center -= dPosC
                self.camera.notify()  # update UI now
            self.previous_mouse = wp
        else:
            # self.messageSent.emit(f'Window Position: {wp.x}, {wp.y}', 500)
            self.messageSent.emit(f'Canvas Position: {cp.x: 0.4f}, {cp.y: 0.4f}', 500)
            # fip = FractionalImagePos.from_CanvasPos(cp, self.image.transform)
            # self.messageSent.emit(f'Fractional Image Position: {fip.x: 0.4f}, {fip.y: 0.4f}', 500)

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
        self.markers.paintGL()

    def resizeGL(self, width: int, height: int) -> None:
        self.aspect_ratio = height/width
