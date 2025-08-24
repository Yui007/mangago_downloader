"""
Worker threads for handling background tasks in the GUI.
"""
import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
import httpx

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.utils import get_headers


class WorkerSignals(QObject):
    """Defines signals available from a running worker thread."""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class ImageDownloader(QRunnable):
    """Worker thread for downloading images."""
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            with httpx.Client(headers=get_headers()) as client:
                response = client.get(self.url, timeout=20)
                response.raise_for_status()
                self.signals.result.emit(response.content)
        except Exception as e:
            self.signals.error.emit((e,))
        finally:
            self.signals.finished.emit()