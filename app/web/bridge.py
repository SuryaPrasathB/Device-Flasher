from PySide6.QtCore import QObject, Signal, Slot
import json
import asyncio

class WebBridge(QObject):
    """
    Acts as a thread-safe two-way communication bridge between the PySide6 main UI thread
    and the background FastAPI/WebSocket server thread.
    """
    # Signals strictly for sending data FROM backend to GUI (Thread Safe)
    web_client_connected = Signal(str) # client_id
    web_client_disconnected = Signal(str) # client_id

    # Global messages (e.g. notifications)
    send_log = Signal(str, str) # message, level

    # Web Action Requests (From Web to GUI)
    request_set_slave_id = Signal(int, int) # old_id, new_id
    request_start_slave_tester = Signal(int) # slave_id
    request_start_stress_tester = Signal(int, int, int, int, str) # from_id, to_id, reg, delay_ms, data_type
    request_stop_stress_tester = Signal()

    # GUI state updates (From GUI to Web)
    # The FastAPI server needs to be able to listen to these.
    # Since FastAPI runs in a separate thread and uses asyncio, we will maintain an
    # asyncio event loop queue or callback list to push these messages into the WS connections.
    gui_state_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._async_callbacks = []

    def register_async_callback(self, callback):
        """
        Register an async function to be called when the GUI sends a state update.
        """
        self._async_callbacks.append(callback)

    @Slot(dict)
    def emit_gui_state(self, state_dict):
        """
        GUI calls this to push updates to Web Clients.
        """
        self.gui_state_updated.emit(state_dict)

        # Also invoke async callbacks
        for callback in self._async_callbacks:
            try:
                # We need to ensure the callback is executed in the target's event loop.
                # Usually we handle this inside the callback itself.
                callback(state_dict)
            except Exception as e:
                print(f"Error executing web bridge callback: {e}")

# Global instance to be used by both UI and Web Server
web_bridge = WebBridge()
