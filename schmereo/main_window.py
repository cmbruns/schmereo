import pkg_resources

import numpy
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence

from schmereo.recent_file import RecentFileList


class SchmereoMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi(uifile=pkg_resources.resource_stream('schmereo', 'schmereo.ui'), baseinstance=self)
        self.ui.actionQuit.setShortcut(QKeySequence.Quit)  # no effect on Windows
        self.recent_files = RecentFileList(
            open_file_slot=self.load_file,
            settings_key='recent_files',
            menu=self.ui.menuRecent_Files
        )

    @QtCore.pyqtSlot(str)
    def load_file(self, file_name: str, eye=None) -> bool:
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
        print(pixels.shape)
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
