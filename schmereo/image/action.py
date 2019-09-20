from PyQt5 import QtCore, QtWidgets


class AddMarkerAction(QtWidgets.QAction):
    def __init__(self, parent=None, *args, mouse_pos, **kwargs):
        super().__init__(text='Add Marker Here', parent=parent, *args, **kwargs)
