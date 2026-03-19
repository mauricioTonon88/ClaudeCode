import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
)
from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtGui import QFont

from region_selector import RegionSelector
from recorder import Recorder


class ControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._region = None
        self._recorder = Recorder()
        self._selector = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.setWindowTitle("Screen Recorder")
        self.setFixedSize(320, 200)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Status label
        self._status = QLabel("No region selected")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet(
            "background: #2b2b2b; color: #aaa; padding: 8px; border-radius: 6px;"
        )
        layout.addWidget(self._status)

        # Time label
        self._time_label = QLabel("00:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setFont(QFont("monospace", 22, QFont.Weight.Bold))
        self._time_label.setStyleSheet("color: #fff;")
        layout.addWidget(self._time_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self._btn_select = QPushButton("Select Region")
        self._btn_select.setStyleSheet(
            "QPushButton { background: #3a3a3a; color: white; padding: 8px 16px; "
            "border-radius: 6px; border: 1px solid #555; }"
            "QPushButton:hover { background: #4a4a4a; }"
        )
        btn_layout.addWidget(self._btn_select)

        self._btn_record = QPushButton("Record")
        self._btn_record.setEnabled(False)
        self._btn_record.setStyleSheet(
            "QPushButton { background: #c0392b; color: white; padding: 8px 16px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #e74c3c; }"
            "QPushButton:disabled { background: #555; color: #888; }"
        )
        btn_layout.addWidget(self._btn_record)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Dark theme
        self.setStyleSheet("QWidget { background: #1e1e1e; }")

    def _connect_signals(self):
        self._btn_select.clicked.connect(self._on_select_region)
        self._btn_record.clicked.connect(self._on_record_toggle)
        self._recorder.time_updated.connect(self._on_time_update)
        self._recorder.recording_stopped.connect(self._on_recording_stopped)
        self._recorder.error_occurred.connect(self._on_error)

    def _on_select_region(self):
        self.hide()
        QTimer.singleShot(200, self._show_selector)

    def _show_selector(self):
        self._selector = RegionSelector()
        self._selector.region_selected.connect(self._on_region_selected)
        self._selector.selection_cancelled.connect(self._on_selection_cancelled)
        self._selector.show()

    def _on_region_selected(self, rect: QRect):
        self._region = rect
        self._recorder.set_region(rect)
        self._status.setText(f"Region: {rect.width()} x {rect.height()}")
        self._status.setStyleSheet(
            "background: #1a3a1a; color: #6f6; padding: 8px; border-radius: 6px;"
        )
        self._btn_record.setEnabled(True)
        self.show()

    def _on_selection_cancelled(self):
        self.show()

    def _on_record_toggle(self):
        if self._recorder.is_recording():
            self._recorder.stop()
        else:
            self._start_recording()

    def _start_recording(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(folder, f"recording_{timestamp}.mp4")

        self._recorder.start(filepath, fps=30)
        self._btn_record.setText("Stop")
        self._btn_record.setStyleSheet(
            "QPushButton { background: #e67e22; color: white; padding: 8px 16px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #f39c12; }"
        )
        self._btn_select.setEnabled(False)
        self._status.setText(f"Recording → {filepath}")
        self._status.setStyleSheet(
            "background: #3a1a1a; color: #f66; padding: 8px; border-radius: 6px;"
        )

    def _on_time_update(self, elapsed: float):
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        self._time_label.setText(f"{mins:02d}:{secs:02d}")

    def _on_recording_stopped(self, path: str):
        self._btn_record.setText("Record")
        self._btn_record.setStyleSheet(
            "QPushButton { background: #c0392b; color: white; padding: 8px 16px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #e74c3c; }"
        )
        self._btn_select.setEnabled(True)
        self._status.setText(f"Saved: {os.path.basename(path)}")
        self._status.setStyleSheet(
            "background: #1a3a1a; color: #6f6; padding: 8px; border-radius: 6px;"
        )
        self._time_label.setText("00:00")

    def _on_error(self, msg: str):
        self._status.setText(f"Error: {msg}")
        self._status.setStyleSheet(
            "background: #3a1a1a; color: #f66; padding: 8px; border-radius: 6px;"
        )
