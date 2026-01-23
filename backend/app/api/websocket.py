"""WebSocket endpoint for real-time pipeline updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

router = APIRouter()

# Store active connections by thread_id
connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, thread_id: str):
        """Accept and store a new connection."""
        await websocket.accept()
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = set()
        self.active_connections[thread_id].add(websocket)

    def disconnect(self, websocket: WebSocket, thread_id: str):
        """Remove a connection."""
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]

    async def broadcast_to_thread(self, thread_id: str, message: dict):
        """Send message to all connections watching a thread."""
        if thread_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[thread_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[thread_id].discard(conn)

    async def broadcast_all(self, message: dict):
        """Broadcast to all connections."""
        for thread_id in list(self.active_connections.keys()):
            await self.broadcast_to_thread(thread_id, message)


manager = ConnectionManager()


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket endpoint for real-time pipeline updates."""
    await manager.connect(websocket, thread_id)

    try:
        # Send initial state
        from app.agents.pipeline import get_pipeline
        pipeline = get_pipeline()
        state = await pipeline.get_state(thread_id)

        if state:
            await websocket.send_json({
                "type": "initial_state",
                "thread_id": thread_id,
                "state": state,
            })

        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any message (ping/pong or requests)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "get_state":
                    state = await pipeline.get_state(thread_id)
                    await websocket.send_json({
                        "type": "state_update",
                        "thread_id": thread_id,
                        "state": state,
                    })

            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, thread_id)


async def notify_pipeline_update(thread_id: str, status: str, data: dict = None):
    """Send pipeline update notification to connected clients."""
    message = {
        "type": "pipeline_update",
        "thread_id": thread_id,
        "status": status,
        "data": data or {},
    }
    await manager.broadcast_to_thread(thread_id, message)


async def notify_approval_required(thread_id: str, approval_type: str, data: dict = None):
    """Notify that approval is required."""
    message = {
        "type": "approval_required",
        "thread_id": thread_id,
        "approval_type": approval_type,
        "data": data or {},
    }
    await manager.broadcast_to_thread(thread_id, message)
    # Also broadcast to global listeners
    await manager.broadcast_all({
        "type": "new_approval",
        "thread_id": thread_id,
        "approval_type": approval_type,
    })


# Export manager for use in other modules
def get_ws_manager() -> ConnectionManager:
    return manager
