from PyQt5.QtWidgets import QUndoCommand

from schmereo.clip_box import ClipBox
from schmereo.coord_sys import ImagePixelCoordinate, FractionalImagePos
from schmereo.image.aligner import Aligner


class AddMarkerCommand(QUndoCommand):
    def __init__(self, widget: 'ImageWidget', marker_pos: ImagePixelCoordinate, parent=None):
        super().__init__(parent)
        self.setText("add marker")
        self.widget = widget
        self.marker_pos = marker_pos

    def redo(self):
        self.widget.add_marker(self.marker_pos)

    def undo(self):
        del self.widget.markers[-1]
        self.widget.update()


class AdjustClipBoxCommand(QUndoCommand):
    def __init__(self, clip_box: ClipBox, old_state, new_state, parent=None):
        super().__init__(parent)
        self.setText("adjust size")
        self.clip_box = clip_box
        self.old_state = old_state
        self.new_state = new_state

    def redo(self):
        self.clip_box.state = self.new_state
        self.clip_box.recenter()
        self.clip_box._dirty = True
        self.clip_box.notify()

    def undo(self):
        self.clip_box.state = self.old_state
        self.clip_box.recenter()
        self.clip_box._dirty = True
        self.clip_box.notify()


class AlignNowCommand(QUndoCommand):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setText("align images")
        self.aligner = Aligner(main_window)
        self.main_window = main_window
        self.old_centers = [w.image.transform.center[:] for w in main_window.eye_widgets()]
        self.old_rotations = [w.image.transform.rotation for w in main_window.eye_widgets()]

    def redo(self):
        self.aligner.align()
        for w in self.main_window.eye_widgets():
            w.update()

    def undo(self):
        for index, w in enumerate(self.main_window.eye_widgets()):
            w.image.transform.center = FractionalImagePos(*self.old_centers[index])
            w.image.transform.rotation = self.old_rotations[index]
        for w in self.main_window.eye_widgets():
            w.update()


class ClearMarkersCommand(QUndoCommand):
    def __init__(self, left_widget: 'ImageWidget', right_widget: 'ImageWidget', parent=None):
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
