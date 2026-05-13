"""
WebSocket connection manager — handles connect/disconnect/broadcast lifecycle.
"""
import asyncio
import json
import logging
from typing import List, Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:

    def __init__(self):
        self.connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.connections.append(ws)
        logger.info("WS connected — total: %d", len(self.connections))

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            if ws in self.connections:
                self.connections.remove(ws)
        logger.info("WS disconnected — total: %d", len(self.connections))

    async def broadcast(self, message: Dict):
        if not self.connections:
            return
        payload = json.dumps(message)
        dead    = []
        for ws in self.connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self.connections:
                        self.connections.remove(ws)

    async def send_personal(self, ws: WebSocket, message: Dict):
        try:
            await ws.send_text(json.dumps(message))
        except Exception as e:
            logger.warning("send_personal failed: %s", e)

    async def close_all(self):
        async with self._lock:
            for ws in self.connections:
                try: await ws.close()
                except Exception: pass
            self.connections.clear()

    @property
    def count(self) -> int:
        return len(self.connections)
