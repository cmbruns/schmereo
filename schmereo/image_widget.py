from typing import Optional

from PIL import Image
from PyQt5 import QtGui, QtWidgets

from schmereo import Camera
from schmereo.coord_sys import WindowPos, CanvasPos
from schmereo.image import SingleImage


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.camera = Camera()
        self.image = SingleImage(camera=self.camera)
        self.is_dragging = False
        self.previous_mouse: Optional[WindowPos] = None
        self.setAcceptDrops(True)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if self.image.image is None:
            return
        mouse_pos = WindowPos.from_QPoint(event.pos())
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction(text='Add marker here', parent=self))
        menu.addAction(QtWidgets.QAction(text='Split image', parent=self))
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
                self.image.image = Image.open(url.toLocalFile())
                self.image.image_needs_upload = True
                self.update()

    def initializeGL(self) -> None:
        self.image.initializeGL()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if not self.is_dragging:
            return
        if self.previous_mouse is not None:
            print(self.previous_mouse)
            dPosW = WindowPos.from_QPoint(event.pos()) - self.previous_mouse
            dPosC = CanvasPos.from_WindowPos(dPosW, self.camera, self.size())
            self.camera.center -= dPosC
            self.update()
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
        dScale = 1.07 ** -dScale
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
        self.update()

    def paintGL(self) -> None:
        self.image.paintGL()

    def resizeGL(self, width: int, height: int) -> None:
        self.camera.aspect = height/width
