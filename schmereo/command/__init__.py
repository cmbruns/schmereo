from PyQt5.QtWidgets import QUndoCommand

from schmereo.coord_sys import ImagePixelCoordinate, FractionalImagePos
from schmereo.image.image_widget import ImageWidget
from schmereo.image.aligner import Aligner


class AlignNowCommand(QUndoCommand):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setText("align images")
        self.aligner = Aligner(main_window)
        self.main_window = main_window
        self.old_centers = [w.image.transform.center[:] for w in main_window.eye_widgets()]

    def redo(self):
        self.aligner.align()
        for w in self.main_window.eye_widgets():
            w.update()

    def undo(self):
        for index, w in enumerate(self.main_window.eye_widgets()):
            w.image.transform.center = FractionalImagePos(*self.old_centers[index])
        for w in self.main_window.eye_widgets():
            w.update()


class ClearMarkersCommand(QUndoCommand):
    def __init__(self, left_widget: ImageWidget, right_widget: ImageWidget, parent=None):
        super().__init__(parent)
        self.left_widget = left_widget
        self.right_widget = right_widget
        self.old_left = [ImagePixelCoordinate(x, y) for x, y in left_widget.markers.points]
        self.old_right = [ImagePixelCoordinate(x, y) for x, y in right_widget.markers.points]
        self.setText("clear markers")

    def redo(self):
        self.left_widget.markers.clear()
        self.right_widget.markers.clear()
        self.left_widget.update()
        self.right_widget.update()

    def undo(self):
        self.left_widget.markers.clear()
        self.right_widget.markers.clear()
        self.left_widget.markers.add_markers(self.old_left)
        self.right_widget.markers.add_markers(self.old_right)
        self.left_widget.update()
        self.right_widget.update()
