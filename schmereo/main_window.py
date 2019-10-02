import inspect
import pkg_resources

import numpy
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

from schmereo.camera import Camera
from schmereo.coord_sys import FractionalImagePos, ImagePixelCoordinate, CanvasPos
from schmereo.image.image_saver import ImageSaver
from schmereo.recent_file import RecentFileList
from schmereo.version import __version__


class SchmereoMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi(uifile=pkg_resources.resource_stream('schmereo', 'schmereo.ui'), baseinstance=self)
        # Platform-specific semantic keyboard shortcuts cannot be set in Qt Designer
        self.ui.actionOpen.setShortcut(QKeySequence.Open)
        self.ui.actionSave_Images.setShortcut(QKeySequence.SaveAs)  # TODO: project files...
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
        self.zoom_increment = 1.10
        self.image_saver = ImageSaver(self.ui.leftImageWidget, self.ui.rightImageWidget)
        # TODO: object for AddMarker tool button
        tb = self.ui.toolButton
        tb.setDefaultAction(self.ui.actionAdd_Marker)
        sz = 32
        tb.setFixedSize(sz, sz)
        tb.setIconSize(QtCore.QSize(sz, sz))
        # tb.setDragEnabled(True)  # TODO: drag tool button to place marker

    def eye_widgets(self):
        for w in (self.ui.leftImageWidget, self.ui.rightImageWidget):
            yield w

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Escape:
            # clear add-marker mode
            self.ui.actionAdd_Marker.setChecked(False)

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
    def on_actionAbout_Schmereo_triggered(self):
        QtWidgets.QMessageBox.about(
            self, 'About Schmereo',
            inspect.cleandoc(f'''
            Schmereo stereograph restoration application.
            By Christopher M. Bruns
            Version {__version__}
            '''),
        )

    @QtCore.pyqtSlot(bool)
    def on_actionAdd_Marker_toggled(self, checked):
        for w in self.eye_widgets():
            w.set_add_marker_mode(checked)
        # TODO: not if that widget has more than the others...

    @QtCore.pyqtSlot()
    def on_actionAlign_Now_triggered(self):
        lwidg = self.ui.leftImageWidget
        rwidg = self.ui.rightImageWidget
        lm = lwidg.markers
        rm = rwidg.markers
        cm = min(len(lm), len(rm))
        if cm < 1:
            return
        # TODO: rotation
        # compute translation
        dy = 0.0
        dx = 0.0
        for i in range(cm):
            dx += (rm[i][0] - lm[i][0]) / cm  # average  TODO: max? min?
            dy += (rm[i][1] - lm[i][1]) / cm  # average
        # convert current center difference to image pixels
        c_c = CanvasPos(0, 0)  # center of image is canvas 0, 0
        lc_i = lwidg.image_from_canvas(c_c)
        rc_i = rwidg.image_from_canvas(c_c)
        desired = ImagePixelCoordinate(dx, dy)
        current = rc_i - lc_i
        change = desired - current
        # Apply half to each eye image
        change2 = ImagePixelCoordinate(0.5 * change.x, 0.5 * change.y)
        lc_i -= change2
        lc_f = lwidg.fract_from_image(lc_i)
        lwidg.image.transform.center = lc_f
        rc_i += change2
        rc_f = rwidg.fract_from_image(rc_i)
        rwidg.image.transform.center = rc_f
        lwidg.update()
        rwidg.update()

    @QtCore.pyqtSlot()
    def on_actionClear_Markers_triggered(self):
        for w in self.eye_widgets():
            w.markers.clear()
        for w in self.eye_widgets():
            w.update()

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

    @QtCore.pyqtSlot()
    def on_actionQuit_triggered(self):
        QtCore.QCoreApplication.quit()

    @QtCore.pyqtSlot()
    def on_actionReport_a_Problem_triggered(self):
        url = QtCore.QUrl('https://github.com/cmbruns/schmereo/issues')
        QtGui.QDesktopServices.openUrl(url)

    @QtCore.pyqtSlot()
    def on_actionSave_Images_triggered(self):
        if not self.image_saver.can_save():
            return
        file_name, file_type = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save File(s)',
            filter='3D Images (*.pns *.jps)',
        )
        if file_name is None:
            return
        if len(file_name) < 1:
            return
        self.image_saver.save_image(file_name, file_type)

    @QtCore.pyqtSlot()
    def on_actionZoom_In_triggered(self):
        self.zoom(amount=self.zoom_increment)

    @QtCore.pyqtSlot()
    def on_actionZoom_Out_triggered(self):
        self.zoom(amount=1.0/self.zoom_increment)

    @QtCore.pyqtSlot()
    def zoom(self, amount: float):
        # In case the zoom is not linked between the two image widgets...
        widgets = (self.ui.leftImageWidget, self.ui.rightImageWidget)
        # store zoom values in case the cameras are all the same
        zooms = [w.camera.zoom for w in widgets]
        for idx, w in enumerate(widgets):
            w.camera.zoom = zooms[idx] * amount
        for w in widgets:
            w.camera.notify()  # repaint now
