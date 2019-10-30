import sys
from PyQt5 import QtGui
from schmereo.application import SchmereoApplication


def main():
    import schmereo.excepthook
    gl_format = QtGui.QSurfaceFormat()
    gl_format.setMajorVersion(4)
    gl_format.setMinorVersion(6)
    gl_format.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    gl_format.setSamples(8)
    QtGui.QSurfaceFormat.setDefaultFormat(gl_format)
    SchmereoApplication()
    sys.exit(0)


if __name__ == "__main__":
    main()
