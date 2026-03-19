#!/usr/bin/env python3
"""Simple screen region recorder."""

import sys
from PyQt6.QtWidgets import QApplication
from ui import ControlWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Screen Recorder")

    window = ControlWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
