import pkg_resources

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence


class SchmereoMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi(uifile=pkg_resources.resource_stream('schmereo', 'schmereo.ui'), baseinstance=self)
        self.ui.actionQuit.triggered.connect(QtCore.QCoreApplication.quit)
        self.ui.actionQuit.setShortcut(QKeySequence.Quit)  # no effect on Windows
