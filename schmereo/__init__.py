import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from schmereo.coord_sys import CanvasPos
from schmereo.main_window import SchmereoMainWindow


class SchmereoApplication(QtWidgets.QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setOrganizationName('rotatingpenguin.com')
        self.setApplicationName('schmereo')
        main_win = SchmereoMainWindow()
        main_win.show()
        sys.exit(self.exec_())


def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


def run_schmereo():
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook
    gl_format = QtGui.QSurfaceFormat()
    gl_format.setMajorVersion(4)
    gl_format.setMinorVersion(6)
    gl_format.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    gl_format.setSamples(4)
    QtGui.QSurfaceFormat.setDefaultFormat(gl_format)
    SchmereoApplication()


if __name__ == '__main__':
    run_schmereo()
