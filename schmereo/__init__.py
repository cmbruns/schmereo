import sys

from PyQt5 import QtGui, QtWidgets

from schmereo.coord_sys import CanvasPos
from schmereo.main_window import SchmereoMainWindow


class SchmereoApplication(QtWidgets.QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setOrganizationName("rotatingpenguin.com")
        self.setApplicationName("schmereo")
        self.setApplicationDisplayName("Schmereo")
        main_win = SchmereoMainWindow()
        main_win.show()
        sys.exit(self.exec_())


def run_schmereo():
    import schmereo.excepthook
    gl_format = QtGui.QSurfaceFormat()
    gl_format.setMajorVersion(4)
    gl_format.setMinorVersion(6)
    gl_format.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    gl_format.setSamples(8)
    QtGui.QSurfaceFormat.setDefaultFormat(gl_format)
    SchmereoApplication()


if __name__ == "__main__":
    run_schmereo()
