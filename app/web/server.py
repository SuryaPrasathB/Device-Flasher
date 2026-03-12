from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import json
import os
import secrets

from app.web.bridge import web_bridge
from app.utils.config import config
from app.utils.logger import logger
from app.utils.helpers import get_resource_path

app = FastAPI(title="LDU Tester Remote API")

# Allow all origins for dev and local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PIN Authentication setup
PIN_CODE = secrets.token_hex(2) # Generate 4 char random hex as default if not set
config_pin = config.get("web_pin", default=None)
if config_pin:
    PIN_CODE = str(config_pin)
logger.info(f"Web Access PIN code: {PIN_CODE}")

class LoginRequest(BaseModel):
    pin: str

@app.post("/api/login")
async def login(req: LoginRequest):
    if req.pin == PIN_CODE:
        return {"status": "success", "token": PIN_CODE} # Simple token for now
    raise HTTPException(status_code=401, detail="Invalid PIN")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New web client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Web client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send to websocket: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# Background task to push updates from GUI to Web Clients
def handle_gui_state_update(state_dict):
    """
    Called by PySide thread via signal -> bridge -> here.
    Needs to run in the asyncio event loop.
    """
    if manager.loop and manager.loop.is_running():
        try:
            # Schedule the broadcast in the running asyncio loop
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(json.dumps({"type": "state_update", "data": state_dict})),
                manager.loop
            )
        except Exception as e:
            logger.error(f"Error scheduling broadcast: {e}")

web_bridge.register_async_callback(handle_gui_state_update)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    # Require token authentication
    if token != PIN_CODE:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Capture loop for broadcasting later
    manager.loop = asyncio.get_running_loop()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                payload = msg.get("payload", {})

                # Route Web actions to GUI thread via bridge signals
                if action == "set_slave_id":
                    web_bridge.request_set_slave_id.emit(payload.get("id", 1))
                elif action == "start_slave_tester":
                    web_bridge.request_start_slave_tester.emit(payload.get("slave_id", 1))
                elif action == "start_stress_tester":
                    web_bridge.request_start_stress_tester.emit(
                        payload.get("from_id", 1),
                        payload.get("to_id", 10),
                        payload.get("reg", 0),
                        payload.get("delay_ms", 1000),
                        payload.get("data_type", "Integer (16-bit)")
                    )
                elif action == "stop_stress_tester":
                    web_bridge.request_stop_stress_tester.emit()
                elif action == "request_state":
                    # The client asked for a full state sync.
                    # We can emit a signal for the GUI to send it down
                    pass # GUI will handle periodic state updates or we can force sync

            except json.JSONDecodeError:
                logger.error("Received invalid JSON on websocket")
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

from fastapi.responses import FileResponse

# Serve the compiled React Frontend from resources/web
frontend_path = get_resource_path("resources/web")
if os.path.exists(frontend_path) and os.path.isdir(frontend_path):
    # Serve static assets (JS, CSS) under /assets
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)
else:
    @app.get("/{full_path:path}")
    def no_frontend():
        return {"message": "Frontend not built yet. Run the React build process."}
