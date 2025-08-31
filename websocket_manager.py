from fastapi import WebSocket
from typing import List
import json

class ConnectionManager:
    def __init__(self):
        # store tuple (websocket, role)
        self.active_connections: List[tuple[WebSocket, str]] = []

    async def connect(self, websocket: WebSocket, role: str):
        await websocket.accept()
        self.active_connections.append((websocket, role))

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            (ws, role) for ws, role in self.active_connections if ws != websocket
        ]

    async def broadcast(self, message: dict, role: str | None = None):
        """
        Send message to all connections.
        If role is provided, send only to that role.
        """
        data = json.dumps(message)
        for ws, ws_role in self.active_connections:
            if role is None or ws_role == role:
                await ws.send_text(data)

# initialize
manager = ConnectionManager()
