import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AdminConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Admin WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass
        logger.info(f"Admin WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def broadcast_from_thread(self, message: dict):
        """Thread-safe broadcast for use from MQTT listener thread."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(message),
                self._loop
            )


manager = AdminConnectionManager()
