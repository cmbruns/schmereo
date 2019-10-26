from PyQt5 import QtCore

from schmereo.coord_sys import CanvasPos


class Camera(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self._zoom = 1.0
        self._center = CanvasPos(0, 0)
        self._dirty = True

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value: CanvasPos):
        if self._center == value:
            return
        self._center = value
        self._dirty = True

    changed = QtCore.pyqtSignal()

    def notify(self):
        if self._dirty:
            self.changed.emit()
        self._dirty = False

    def reset(self):
        self._zoom = 1.0
        self._center = CanvasPos(0, 0)
        self._dirty = True

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value: float):
        if value < 0.25:
            value = 0.25
        if self._zoom == value:
            return
        self._zoom = value
        self._dirty = True
