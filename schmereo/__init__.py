import sys
import traceback
from PyQt5 import QtCore, QtWidgets, uic


sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class SchmereoApp(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('schmereo.ui', self)


if __name__ == '__main__':
    sys.excepthook = exception_hook
    app = QtWidgets.QApplication(sys.argv)
    main_win = SchmereoApp()
    main_win.show()
    sys.exit(app.exec_())
