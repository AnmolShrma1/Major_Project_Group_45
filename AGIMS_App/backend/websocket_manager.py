"""
WebSocket connection manager for live data streaming
"""
from fastapi import WebSocket
from typing import List, Dict
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for live data streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        print(f"✓ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"✗ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        # Convert message to JSON
        json_message = json.dumps(message)
        
        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        if disconnected:
            async with self.lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)
    
    async def send_personal(self, websocket: WebSocket, message: Dict):
        """Send message to a specific client"""
        try:
            json_message = json.dumps(message)
            await websocket.send_text(json_message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    async def close_all(self):
        """Close all active connections"""
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.close()
                except Exception:
                    pass
            self.active_connections.clear()