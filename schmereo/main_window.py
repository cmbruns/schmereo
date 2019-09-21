import pkg_resources

import numpy
from PIL import Image
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QKeySequence

from schmereo.camera import Camera
from schmereo.coord_sys import FractionalImagePos, PixelCoordinate
from schmereo.marker import Marker, MarkerPair
from schmereo.recent_file import RecentFileList


class SchmereoMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi(uifile=pkg_resources.resource_stream('schmereo', 'schmereo.ui'), baseinstance=self)
        # Platform-specific semantic keyboard shortcuts cannot be set in Qt Designer
        self.ui.actionQuit.setShortcut(QKeySequence.Quit)  # no effect on Windows
        self.ui.actionZoom_In.setShortcuts([QKeySequence.ZoomIn, 'Ctrl+='])  # '=' so I don't need to press SHIFT
        self.ui.actionZoom_Out.setShortcut(QKeySequence.ZoomOut)
        #
        self.recent_files = RecentFileList(
            open_file_slot=self.load_file,
            settings_key='recent_files',
            menu=self.ui.menuRecent_Files
        )
        # Link views
        self.shared_camera = Camera()
        self.ui.leftImageWidget.camera = self.shared_camera
        self.ui.rightImageWidget.camera = self.shared_camera
        #
        self.ui.leftImageWidget.file_dropped.connect(self.load_left_file)
        self.ui.rightImageWidget.file_dropped.connect(self.load_right_file)
        #
        self.ui.leftImageWidget.image.transform.center = FractionalImagePos(-0.5, 0)
        self.ui.rightImageWidget.image.transform.center = FractionalImagePos(+0.5, 0)
        #
        for w in (self.ui.leftImageWidget, self.ui.rightImageWidget):
            w.messageSent.connect(self.ui.statusbar.showMessage)
        #
        self.marker_set = list()
        self.marker_set.append(MarkerPair(
            left=Marker(PixelCoordinate(1443, 1937)),
            right=Marker(PixelCoordinate(3657, 1925))))

    def load_left_file(self, file_name: str) -> None:
        self.load_file(file_name)

    def load_right_file(self, file_name: str) -> None:
        self.load_file(file_name)

    @QtCore.pyqtSlot(str)
    def load_file(self, file_name: str) -> bool:
        result = False
        self.log_message(f'Loading file {file_name}...')
        image = Image.open(file_name)
        if image is None:
            self.log_message(f'ERROR: Image load failed.')
            return False
        self.log_message(f'Processing image {file_name}...')
        pixels = numpy.frombuffer(buffer=image.convert('RGBA').tobytes(), dtype=numpy.ubyte)
        if pixels is None or len(pixels) < 1:
            self.log_message(f'ERROR: Image processing failed.')
            return False
        self.log_message(f'Finished processing image {file_name}')
        result = self.ui.leftImageWidget.load_image(file_name, image, pixels)
        if result:
            result = self.ui.rightImageWidget.load_image(file_name, image, pixels)
        if result:
            self.ui.leftImageWidget.update()
            self.ui.rightImageWidget.update()
            self.recent_files.add_file(file_name)
        else:
            self.log_message(f'ERROR: Image load failed.')
        return result

    def log_message(self, message: str) -> None:
        self.ui.statusbar.showMessage(message)

    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        file_name, file_type = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='caption',
            filter='Images (*.tif);;All Files (*)')
        if file_name is None:
            return
        if len(file_name) < 1:
            return
        self.load_file(file_name)

    @staticmethod
    @QtCore.pyqtSlot()
    def on_actionQuit_triggered():
        QtCore.QCoreApplication.quit()

    def on_actionZoom_In_triggered(self):
        self.zoom(amount=1.0/1.1)

    def on_actionZoom_Out_triggered(self):
        self.zoom(amount=1.1)

    def zoom(self, amount: float):
        # In case the zoom is not linked between the two image widgets...
        widgets = (self.ui.leftImageWidget, self.ui.rightImageWidget)
        # store zoom values in case the cameras are all the same
        zooms = [w.camera.zoom for w in widgets]
        for idx, w in enumerate(widgets):
            w.camera.zoom = zooms[idx] * amount
        for w in widgets:
            w.camera.notify()  # repaint now
