from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from schmereo.camera import Camera
from schmereo.coord_sys import WindowPos, CanvasPos
from schmereo.image import SingleImage
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

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if not self.is_dragging:
            return
        if self.previous_mouse is not None:
            dPosW = WindowPos.from_QPoint(event.pos()) - self.previous_mouse
            dPosC = CanvasPos.from_WindowPos(dPosW, self.camera, self.size())
            self.camera.center -= dPosC
            self.camera.notify()  # update UI now
        self.previous_mouse = WindowPos.from_QPoint(event.pos())

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
            window_center = WindowPos(self.width()/2.0, self.height()/2.0)
            mouse_pos = WindowPos.from_QPoint(event.pos())
            rel_posW = mouse_pos - window_center
            start_posC = CanvasPos.from_WindowPos(rel_posW, self.camera, self.size())
            self.camera.zoom *= dScale
            end_posC = CanvasPos.from_WindowPos(rel_posW, self.camera, self.size())
            self.camera.center += (start_posC - end_posC)
        else:
            # zoom centered on widget center
            self.camera.zoom *= dScale
        self.camera.notify()

    def paintGL(self) -> None:
        self.image.paintGL(self.aspect_ratio)
        self.markers.paintGL()

    def resizeGL(self, width: int, height: int) -> None:
        self.aspect_ratio = height/width
