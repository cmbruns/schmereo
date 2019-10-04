from PyQt5.QtCore import pyqtSlot, QObject


class MarkerManager(QObject):
    def __init__(self, main_window):
        super().__init__(parent=main_window)
        self.main_window = main_window
        ama = main_window.ui.actionAdd_Marker
        ama.toggled.connect(self.on_actionAdd_Marker_toggled)
        self.actionAdd_Marker = ama
        self.widgets = list(main_window.eye_widgets())
        main_window.ui.actionHand_Mode.triggered.connect(
            self.on_actionHand_Mode_triggered
        )
        for w in self.widgets:
            w.marker_added.connect(self.on_marker_added)

    @pyqtSlot(bool)
    def on_actionAdd_Marker_toggled(self, toggled):
        if toggled:
            min_markers = None
            for w in self.widgets:
                if min_markers is None:
                    min_markers = len(w.markers)
                    continue
                min_markers = min(min_markers, len(w.markers))
            for w in self.widgets:
                if len(w.markers) == min_markers:
                    w.set_add_marker_mode(True)
                else:
                    w.set_add_marker_mode(False)
        else:
            for w in self.widgets:
                w.set_add_marker_mode(False)

    @pyqtSlot()
    def on_actionHand_Mode_triggered(self):
        self.set_marker_mode(False)

    @pyqtSlot()
    def on_marker_added(self):
        if len(self.widgets[0].markers) == len(self.widgets[1].markers):
            self.set_marker_mode(False)

    def set_marker_mode(self, mode_on=True):
        self.actionAdd_Marker.setChecked(mode_on)
