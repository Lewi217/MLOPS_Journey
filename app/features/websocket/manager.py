import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str = "global") -> None:
        await websocket.accept()
        self._rooms.setdefault(room_id, set()).add(websocket)
        logger.info("WS connected  room=%s total=%d", room_id, len(self._rooms[room_id]))

    def disconnect(self, websocket: WebSocket, room_id: str = "global") -> None:
        room = self._rooms.get(room_id, set())
        room.discard(websocket)
        if not room:
            self._rooms.pop(room_id, None)
        logger.info("WS disconnect room=%s remaining=%d", room_id, len(room))

    async def send_personal(self, data: Any, websocket: WebSocket) -> None:
        payload = data if isinstance(data, str) else json.dumps(data)
        await websocket.send_text(payload)

    async def broadcast_room(self, data: Any, room_id: str = "global") -> None:
        payload = data if isinstance(data, str) else json.dumps(data)
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(room_id, set())):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room_id)

    async def broadcast_all(self, data: Any) -> None:
        for room_id in list(self._rooms):
            await self.broadcast_room(data, room_id)

    async def start_pubsub_listener(self, redis: Redis, channel: str = "ws:broadcast") -> None:
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info("Redis Pub/Sub listener started on channel '%s'", channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                raw_data = message["data"]
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode("utf-8")
                try:
                    parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    target_room = parsed.get("room") if isinstance(parsed, dict) else None
                    if target_room:
                        await self.broadcast_room(parsed, target_room)
                    else:
                        await self.broadcast_all(parsed)
                except Exception:
                    await self.broadcast_all(raw_data)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            logger.info("Redis Pub/Sub listener stopped")

    @property
    def active_rooms(self) -> dict[str, int]:
        return {room: len(conns) for room, conns in self._rooms.items()}


manager = ConnectionManager()
