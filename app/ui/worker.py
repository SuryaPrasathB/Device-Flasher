from PySide6.QtCore import QObject, Signal, QThread
from app.core.flash_service import FlashService

class FlashWorker(QObject):
    """
    Worker class to run the flashing process in a separate thread.
    """
    finished = Signal(bool, str) # success, message
    progress = Signal(str, int)  # message, percentage
    
    def __init__(self, port, slave_id):
        super().__init__()
        self.port = port
        self.slave_id = slave_id
        self.service = FlashService()
        
    def run(self):
        success, message = self.service.flash_device(
            self.port, 
            self.slave_id, 
            progress_callback=self._emit_progress
        )
        self.finished.emit(success, message)
        
    def _emit_progress(self, msg, pct):
        self.progress.emit(msg, pct)
