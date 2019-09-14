import sys
import traceback

import numpy
from PyQt5 import QtGui, QtWidgets, uic


def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class SchmereoApp(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('schmereo.ui', self)


if __name__ == '__main__':
    sys._excepthook = sys.excepthook
    sys.excepthook = exception_hook

    gl_format = QtGui.QSurfaceFormat()
    gl_format.setMajorVersion(4)
    gl_format.setMinorVersion(6)
    gl_format.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    gl_format.setSamples(4)
    QtGui.QSurfaceFormat.setDefaultFormat(gl_format);

    app = QtWidgets.QApplication(sys.argv)
    main_win = SchmereoApp()
    main_win.show()
    sys.exit(app.exec_())


class Camera(object):
    def __init__(self):
        self.aspect = 1.0
        self.zoom = 1.0
        self.center = numpy.array((0, 0), dtype=numpy.float32)