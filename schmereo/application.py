import sys

from PyQt5 import QtWidgets

from .main_window import SchmereoMainWindow


# https://github.com/winpython/winpython/issues/613
def hack_around_opengl_bug():
    import numpy
    if not hasattr(numpy, "float128"):
        numpy.float128 = numpy.longfloat
    if not hasattr(numpy, "complex256"):
        numpy.complex256 = numpy.complex128


class SchmereoApplication(QtWidgets.QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        hack_around_opengl_bug()
        self.setOrganizationName("rotatingpenguin.com")
        self.setApplicationName("schmereo")
        self.setApplicationDisplayName("Schmereo")
        main_win = SchmereoMainWindow()
        main_win.show()
        sys.exit(self.exec_())
