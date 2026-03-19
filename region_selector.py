from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QGuiApplication


class RegionSelector(QWidget):
    region_selected = pyqtSignal(QRect)
    selection_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._start = QPoint()
        self._end = QPoint()
        self._selecting = False

        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._info_label = QLabel(self)
        self._info_label.setStyleSheet(
            "background: rgba(0,0,0,180); color: white; padding: 4px 8px; "
            "border-radius: 4px; font-size: 13px;"
        )
        self._info_label.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end = event.pos()
            rect = self._current_rect()
            self._info_label.setText(f"  {rect.width()} x {rect.height()}  ")
            self._info_label.adjustSize()
            self._info_label.move(event.pos().x() + 15, event.pos().y() + 15)
            self._info_label.show()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            rect = self._current_rect()
            if rect.width() > 10 and rect.height() > 10:
                self.region_selected.emit(rect)
                self.close()
            else:
                self._info_label.hide()
                self.update()

    def _current_rect(self):
        return QRect(self._start, self._end).normalized()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._selecting or (self._start != self._end):
            rect = self._current_rect()
            # Clear the selected region (make it transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw border around selection
            pen = QPen(QColor(0, 120, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

        painter.end()
