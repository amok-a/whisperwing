from PyQt6.QtCore import QObject, pyqtSignal


class Signals(QObject):
    transcript_line = pyqtSignal(str)
    explanation_ready = pyqtSignal(str)
    screen_explanation_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)