import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}  # session_id -> [websockets]
        self._loop: asyncio.AbstractEventLoop | None = None
    
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
    
    async def connect(self, session_id: int, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session {session_id}. Total: {len(self.active_connections[session_id])}")
    
    def disconnect(self, session_id: int, websocket: WebSocket):
        if session_id in self.active_connections:
            try:
                self.active_connections[session_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def broadcast_to_session(self, session_id: int, message: dict):
        connections = self.active_connections.get(session_id, [])
        disconnected = []
        for connection in list(connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(session_id, conn)
    
    def broadcast_from_thread(self, session_id: int, message: dict):
        """Thread-safe broadcast for use from MQTT listener thread."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_to_session(session_id, message),
                self._loop
            )

manager = ConnectionManager()
