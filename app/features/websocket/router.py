import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.features.websocket.manager import manager

router = APIRouter()

WS_PUBSUB_CHANNEL = "ws:broadcast"


async def _publish_or_broadcast(redis: Redis, event: dict, room_id: str) -> None:
    try:
        await redis.publish(WS_PUBSUB_CHANNEL, json.dumps(event))
    except Exception:
        await manager.broadcast_room(event, room_id)


@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    redis: Redis = Depends(get_redis),
):
    await manager.connect(websocket, room_id)
    join_event = {"event": "join", "room": room_id, "message": f"A user joined '{room_id}'"}
    await _publish_or_broadcast(redis, join_event, room_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"text": raw}

            event = {"event": "message", "room": room_id, "data": payload}
            await _publish_or_broadcast(redis, event, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        leave_event = {"event": "leave", "room": room_id, "message": "A user left"}
        await _publish_or_broadcast(redis, leave_event, room_id)


@router.get("/status", tags=["WebSockets"])
async def ws_status():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"rooms": manager.active_rooms},
    )


@router.post("/broadcast/{room_id}", tags=["WebSockets"])
async def http_broadcast(
    room_id: str,
    body: dict,
    redis: Redis = Depends(get_redis),
):
    event = {"event": "server_broadcast", "room": room_id, "data": body}
    await _publish_or_broadcast(redis, event, room_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"sent": True, "room": room_id},
    )
