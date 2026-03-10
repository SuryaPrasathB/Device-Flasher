import uvicorn
import threading
from pyngrok import ngrok
from PySide6.QtCore import QObject, Signal, Slot
from app.utils.logger import logger
from app.web.server import app, PIN_CODE

class WebServerManager(QObject):
    server_started = Signal(str, str) # url, pin
    server_error = Signal(str)

    def __init__(self, port=8000):
        super().__init__()
        self.port = port
        self.server_thread = None
        self.ngrok_tunnel = None
        self.uvicorn_server = None
        self._is_running = False

    def start_server(self, use_ngrok=True):
        if self._is_running:
            return

        def run_uvicorn():
            try:
                config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="error")
                self.uvicorn_server = uvicorn.Server(config)
                self.uvicorn_server.run()
            except Exception as e:
                self.server_error.emit(f"Uvicorn Error: {e}")

        self.server_thread = threading.Thread(target=run_uvicorn, daemon=True)
        self.server_thread.start()
        self._is_running = True

        url = f"http://localhost:{self.port}"
        if use_ngrok:
            try:
                self.ngrok_tunnel = ngrok.connect(self.port)
                url = self.ngrok_tunnel.public_url
                logger.info(f"Ngrok tunnel established: {url}")
            except Exception as e:
                logger.error(f"Ngrok connection failed: {e}")
                self.server_error.emit(f"Ngrok failed: {e}. Falling back to localhost.")

        self.server_started.emit(url, PIN_CODE)

    def stop_server(self):
        if self.ngrok_tunnel:
            ngrok.disconnect(self.ngrok_tunnel.public_url)
            self.ngrok_tunnel = None

        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True

        self._is_running = False
        logger.info("Web Server Stopped.")
