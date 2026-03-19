import time
import threading
import numpy as np
import cv2
import mss
from PyQt6.QtCore import QRect, QObject, pyqtSignal


class Recorder(QObject):
    recording_stopped = pyqtSignal(str)  # emits file path
    error_occurred = pyqtSignal(str)
    time_updated = pyqtSignal(float)  # elapsed seconds

    def __init__(self):
        super().__init__()
        self._recording = False
        self._thread = None
        self._region = None
        self._output_path = None
        self._fps = 30

    def set_region(self, rect: QRect):
        self._region = {
            "left": rect.x(),
            "top": rect.y(),
            "width": rect.width(),
            "height": rect.height(),
        }

    def start(self, output_path: str, fps: int = 30):
        if self._region is None:
            self.error_occurred.emit("No region selected.")
            return
        self._output_path = output_path
        self._fps = fps
        self._recording = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._recording = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def is_recording(self):
        return self._recording

    def _capture_loop(self):
        region = self._region
        fps = self._fps
        frame_interval = 1.0 / fps

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            self._output_path,
            fourcc,
            fps,
            (region["width"], region["height"]),
        )

        if not writer.isOpened():
            self.error_occurred.emit(f"Failed to open video writer for {self._output_path}")
            self._recording = False
            return

        start_time = time.monotonic()

        try:
            with mss.mss() as sct:
                while self._recording:
                    frame_start = time.monotonic()

                    img = sct.grab(region)
                    frame = np.array(img)
                    # mss returns BGRA, OpenCV needs BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    writer.write(frame)

                    elapsed = time.monotonic() - start_time
                    self.time_updated.emit(elapsed)

                    # Maintain target FPS
                    sleep_time = frame_interval - (time.monotonic() - frame_start)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            writer.release()
            self._recording = False
            self.recording_stopped.emit(self._output_path)
