import inspect
import json
import pkg_resources

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QUndoStack

from schmereo.camera import Camera
from schmereo.clip_box import ClipBox
from schmereo.command import AlignNowCommand, ClearMarkersCommand
from schmereo.coord_sys import FractionalImagePos, ImagePixelCoordinate, CanvasPos
from schmereo.image.aligner import Aligner
from schmereo.image.image_saver import ImageSaver
from schmereo.marker.marker_manager import MarkerManager
from schmereo.recent_file import RecentFileList
from schmereo.version import __version__


def _set_action_icon(action, package, image, on_image=None):
    fh = pkg_resources.resource_stream(package, image)
    img = ImageQt(Image.open(fh).convert("RGBA"))
    icon = QtGui.QIcon(QtGui.QPixmap.fromImage(img))
    if on_image is not None:
        fh2 = pkg_resources.resource_stream(package, on_image)
        img2 = ImageQt(Image.open(fh2).convert("RGBA"))
        pm = QtGui.QPixmap.fromImage(img2)
        icon.addPixmap(pm, state=QtGui.QIcon.On)
    action.setIcon(icon)


class SchmereoMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi(
            uifile=pkg_resources.resource_stream("schmereo", "schmereo.ui"),
            baseinstance=self,
        )
        # Platform-specific semantic keyboard shortcuts cannot be set in Qt Designer
        self.ui.actionOpen.setShortcut(QKeySequence.Open)
        self.ui.actionSave_Images.setShortcut(
            QKeySequence.SaveAs
        )  # TODO: project files...
        self.ui.actionQuit.setShortcut(QKeySequence.Quit)  # no effect on Windows
        self.ui.actionZoom_In.setShortcuts(
            [QKeySequence.ZoomIn, "Ctrl+="]
        )  # '=' so I don't need to press SHIFT
        self.ui.actionZoom_Out.setShortcut(QKeySequence.ZoomOut)
        self.ui.actionSave_Project_As.setShortcut(QKeySequence.SaveAs)
        #
        self.recent_files = RecentFileList(
            open_file_slot=self.load_file,
            settings_key="recent_files",
            menu=self.ui.menuRecent_Files,
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
        tb = self.ui.addMarkerToolButton
        tb.setDefaultAction(self.ui.actionAdd_Marker)
        sz = 32
        tb.setFixedSize(sz, sz)
        tb.setIconSize(QtCore.QSize(sz, sz))
        hb = self.ui.handModeToolButton
        hb.setDefaultAction(self.ui.actionHand_Mode)
        hb.setFixedSize(sz, sz)
        hb.setIconSize(QtCore.QSize(sz, sz))
        _set_action_icon(
            self.ui.actionAdd_Marker,
            "schmereo.marker",
            "crosshair64.png",
            "crosshair64blue.png",
        )
        _set_action_icon(self.ui.actionHand_Mode, "schmereo", "cursor-openhand20.png")
        # tb.setDragEnabled(True)  # TODO: drag tool button to place marker
        self.marker_manager = MarkerManager(self)
        self.aligner = Aligner(self)
        self.project_file_name = None
        #
        self.undo_stack = QUndoStack(self)
        undo_action = self.undo_stack.createUndoAction(self, '&Undo')
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action = self.undo_stack.createRedoAction(self, '&Redo')
        redo_action.setShortcuts(QKeySequence.Redo)
        self.ui.menuEdit.insertAction(self.ui.actionAlign_Now, undo_action)
        self.ui.menuEdit.insertAction(self.ui.actionAlign_Now, redo_action)
        self.ui.menuEdit.insertSeparator(self.ui.actionAlign_Now)
        clip_box = ClipBox(parent=self)
        for w in self.eye_widgets():
            w.undo_stack = self.undo_stack
            w.clip_box = clip_box
            clip_box.changed.connect(w.update)

    def eye_widgets(self):
        for w in (self.ui.leftImageWidget, self.ui.rightImageWidget):
            yield w

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.marker_manager.set_marker_mode(False)

    def load_left_file(self, file_name: str) -> None:
        self.load_file(file_name)

    def load_right_file(self, file_name: str) -> None:
        self.load_file(file_name)

    @QtCore.pyqtSlot(str)
    def load_file(self, file_name: str) -> bool:
        result = False
        self.log_message(f"Loading file {file_name}...")
        try:
            image = Image.open(file_name)
        except OSError:
            return self.load_project(file_name)
        result = self.ui.leftImageWidget.load_image(file_name)
        if result:
            result = self.ui.rightImageWidget.load_image(file_name)
        if result:
            self.ui.leftImageWidget.update()
            self.ui.rightImageWidget.update()
            self.recent_files.add_file(file_name)
        else:
            self.log_message(f"ERROR: Image load failed.")
        return result

    def load_project(self, file_name):
        with open(file_name, "r") as fh:
            data = json.load(fh)
            self.from_dict(data)
            for w in self.eye_widgets():
                w.update()
            self.recent_files.add_file(file_name)
            self.project_file_name = file_name
            self.ui.actionSave.setEnabled(True)
            self.setWindowFilePath(self.project_file_name)
            return True

    def log_message(self, message: str) -> None:
        self.ui.statusbar.showMessage(message)

    @QtCore.pyqtSlot()
    def on_actionAbout_Schmereo_triggered(self):
        QtWidgets.QMessageBox.about(
            self,
            "About Schmereo",
            inspect.cleandoc(
                f"""
                Schmereo stereograph restoration application
                Version: {__version__}
                Author: Christopher M. Bruns
                Code: https://github.com/cmbruns/schmereo
                """
            ),
        )

    @QtCore.pyqtSlot()
    def on_actionAlign_Now_triggered(self):
        self.undo_stack.push(AlignNowCommand(self))

    @QtCore.pyqtSlot()
    def on_actionClear_Markers_triggered(self):
        self.undo_stack.push(ClearMarkersCommand(*self.eye_widgets()))

    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        file_name, file_type = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Load Image",
            filter="Projects and Images (*.json *.tif);;All Files (*)",
        )
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
        url = QtCore.QUrl("https://github.com/cmbruns/schmereo/issues")
        QtGui.QDesktopServices.openUrl(url)

    @QtCore.pyqtSlot()
    def on_actionSave_triggered(self):
        if self.project_file_name is None:
            return
        self.save_project_file(self.project_file_name)

    @QtCore.pyqtSlot()
    def on_actionSave_Images_triggered(self):
        if not self.image_saver.can_save():
            return
        file_name, file_type = QtWidgets.QFileDialog.getSaveFileName(
            parent=self, caption="Save File(s)", filter="3D Images (*.pns *.jps)"
        )
        if file_name is None:
            return
        if len(file_name) < 1:
            return
        self.image_saver.save_image(file_name, file_type)

    @QtCore.pyqtSlot()
    def on_actionSave_Project_As_triggered(self):
        file_name, file_type = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Project",
            filter="Schmereo Projects (*.json);;All Files (*)",
        )
        if file_name is None:
            return
        if len(file_name) < 1:
            return
        self.save_project_file(file_name)

    @QtCore.pyqtSlot()
    def on_actionZoom_In_triggered(self):
        self.zoom(amount=self.zoom_increment)

    @QtCore.pyqtSlot()
    def on_actionZoom_Out_triggered(self):
        self.zoom(amount=1.0 / self.zoom_increment)

    def save_project_file(self, file_name):
        with open(file_name, "w") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        self.recent_files.add_file(file_name)

    def to_dict(self):
        return {
            "app": {"name": "schmereo", "version": __version__},
            "left": self.ui.leftImageWidget.to_dict(),
            "right": self.ui.rightImageWidget.to_dict(),
        }

    def from_dict(self, data):
        self.ui.leftImageWidget.from_dict(data["left"])
        self.ui.rightImageWidget.from_dict(data["right"])

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
