import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
connected_clients = set()

async def register(websocket):
    connected_clients.add(websocket)
    logger.info(f"Dashboard client connected. Total: {len(connected_clients)}")
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "ChainSight live feed connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "clients": len(connected_clients)
        })
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total: {len(connected_clients)}")

async def broadcast(event: dict):
    global connected_clients
    if not connected_clients:
        return
    disconnected = set()
    for client in connected_clients.copy():
        try:
            await client.send_json(event)
        except Exception:
            disconnected.add(client)
    connected_clients -= disconnected

def broadcast_sync(event: dict):
    global connected_clients
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast(event))
    except Exception as e:
        logger.error(f"Broadcast failed: {e}")
