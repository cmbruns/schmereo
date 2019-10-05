from PyQt5.QtWidgets import QUndoCommand

from schmereo.coord_sys import ImagePixelCoordinate
from schmereo.image.image_widget import ImageWidget


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
