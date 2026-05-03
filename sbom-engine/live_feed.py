"""
live_feed.py
WebSocket server that pushes real-time events to the dashboard.
Every time a session is generated, all connected dashboard clients
receive an instant update without polling.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Store all connected WebSocket clients
connected_clients = set()


async def register(websocket):
    connected_clients.add(websocket)
    logger.info(f"Dashboard client connected. Total: {len(connected_clients)}")
    try:
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'ChainSight live feed connected',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'clients': len(connected_clients)
        }))
        await websocket.wait_closed()
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total: {len(connected_clients)}")


async def broadcast(event: dict):
    """Broadcast an event to all connected dashboard clients."""
    if not connected_clients:
        return
    message = json.dumps(event)
    disconnected = set()
    for client in connected_clients.copy():
        try:
            await client.send(message)
        except Exception:
            disconnected.add(client)
    connected_clients -= disconnected


def broadcast_sync(event: dict):
    """Synchronous wrapper for broadcasting from FastAPI endpoints."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast(event))
        else:
            loop.run_until_complete(broadcast(event))
    except Exception as e:
        logger.error(f"Broadcast failed: {e}")
