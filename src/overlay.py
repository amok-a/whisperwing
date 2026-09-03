from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal


class TitleBar(QWidget):
    """Верхняя полоска окна — за неё окно перетаскивается мышью."""

    def __init__(self, parent_window):
        super().__init__()
        self._parent_window = parent_window
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        title = QLabel("🪶 Whisperwing")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(26)
        close_btn.clicked.connect(parent_window.close)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self._parent_window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class OverlayWindow(QWidget):
    closing = pyqtSignal()

    def __init__(self, signals, on_toggle_listen, on_explain, on_explain_screen):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.resize(360, 480)
        self.setStyleSheet(
            "background-color: #1e1e1e; color: #eee; border-radius: 8px; font-size: 12px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 8)

        layout.addWidget(TitleBar(self))

        self.status_label = QLabel("Статус: выключено")
        self.status_label.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(self.status_label)

        transcript_label = QLabel("Транскрипт:")
        transcript_label.setContentsMargins(8, 4, 8, 0)
        layout.addWidget(transcript_label)

        self.transcript_view = QTextEdit()
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setPlaceholderText("Здесь будет появляться распознанная речь...")
        self.transcript_view.setMaximumHeight(160)
        layout.addWidget(self.transcript_view)

        answer_label = QLabel("Объяснение:")
        answer_label.setContentsMargins(8, 4, 8, 0)
        layout.addWidget(answer_label)

        self.answer_view = QTextEdit()
        self.answer_view.setReadOnly(True)
        self.answer_view.setPlaceholderText("Здесь появится объяснение от LLM...")
        layout.addWidget(self.answer_view)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(8, 4, 8, 0)

        self.listen_btn = QPushButton("▶ Слушать")
        self.listen_btn.clicked.connect(on_toggle_listen)
        buttons.addWidget(self.listen_btn)

        explain_btn = QPushButton("💬 Объяснить")
        explain_btn.clicked.connect(on_explain)
        buttons.addWidget(explain_btn)

        screen_btn = QPushButton("🖼 Экран")
        screen_btn.clicked.connect(on_explain_screen)
        buttons.addWidget(screen_btn)

        layout.addLayout(buttons)

        opacity_row = QHBoxLayout()
        opacity_row.setContentsMargins(8, 4, 8, 4)
        opacity_row.addWidget(QLabel("Прозрачность:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        layout.addLayout(opacity_row)

        signals.transcript_line.connect(self._on_transcript_line)
        signals.explanation_ready.connect(self._on_explanation)
        signals.screen_explanation_ready.connect(self._on_screen_explanation)
        signals.status_changed.connect(self._on_status_changed)

        self.setWindowOpacity(0.95)

    def _on_opacity_changed(self, value):
        self.setWindowOpacity(value / 100)

    def _on_transcript_line(self, text):
        self.transcript_view.append(text)
        scrollbar = self.transcript_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_explanation(self, text):
        self.answer_view.setMarkdown(f"**[Скриншот]**\n\n{text}")

    def _on_screen_explanation(self, text):
        self.answer_view.setMarkdown(f"**[Скриншот]**\n\n{text}")

    def _on_status_changed(self, text):
        self.status_label.setText(f"Статус: {text}")
        if "запущено" in text:
            self.listen_btn.setText("⏸ Остановить")
        elif "остановлено" in text:
            self.listen_btn.setText("▶ Слушать")

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)
