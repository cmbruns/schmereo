from PIL import Image
from PyQt5 import QtGui, QtWidgets


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasImage() or md.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                img = Image.open(url.toLocalFile())
                print(img)

    def initializeGL(self) -> None:
        print('initializeGL')
        pass

    def paintGL(self) -> None:
        pass

    def resizeGL(self, width: int, height: int) -> None:
        pass
