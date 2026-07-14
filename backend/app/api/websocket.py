from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
import logging

from app.services.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def broadcast(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            dead = []
            for ws in self.active_connections[task_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[task_id].discard(ws)

manager = ConnectionManager()

async def notify_task_update(task_id: str, data: dict):
    """Broadcast task update to all connected clients"""
    await manager.broadcast(task_id, {
        "type": "task_update",
        "task_id": task_id,
        "data": data
    })

async def notify_agent_update(task_id: str, agent_type: str, status: str, data: dict = None):
    """Broadcast agent status update"""
    await manager.broadcast(task_id, {
        "type": "agent_update",
        "task_id": task_id,
        "agent_type": agent_type,
        "status": status,
        "data": data or {}
    })

async def notify_log(task_id: str, level: str, message: str, agent: str = None):
    """Broadcast a log entry"""
    await manager.broadcast(task_id, {
        "type": "log",
        "task_id": task_id,
        "level": level,
        "message": message,
        "agent": agent
    })

@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates"""
    await manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send pings or commands
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, task_id)
