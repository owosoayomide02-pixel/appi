from hashlib import sha256
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.database import SessionLocal
from app.models.tables import Device, User
from app.realtime.hub import hub
from app.runtime.capabilities import sanitize_reported_capabilities
from app.security.tokens import decode_access_token

router = APIRouter(tags=["ws"])


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


@router.websocket("/api/v1/ws/ui")
async def ui_socket(ws: WebSocket) -> None:
    await ws.accept()
    token = ws.cookies.get("access_token")
    if not token:
        header = ws.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            token = header.split(" ", 1)[1]
        token = token or ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return
    try:
        user_id = decode_access_token(token).get("sub")
    except InvalidTokenError:
        await ws.close(code=4401)
        return
    await hub.register_ui(user_id, ws)
    try:
        await ws.send_json({"type": "hello", "channel": "ui"})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.unregister_ui(user_id, ws)


@router.websocket("/api/v1/ws/device")
async def device_socket(ws: WebSocket) -> None:
    await ws.accept()
    token = ws.query_params.get("token") or ""
    if not token:
        await ws.close(code=4401)
        return
    async with SessionLocal() as db:
        device = (await db.execute(select(Device).where(Device.token_hash == _hash(token)))).scalar_one_or_none()
        if not device:
            await ws.close(code=4401)
            return
        if device.revoked_at:
            await ws.close(code=4403)
            return
        device.status = "online"
        device.last_seen_at = datetime.now(UTC)
        user = await db.get(User, device.user_id)
        await db.commit()
        device_id = device.id
        user_id = device.user_id
        killed = bool(user and user.kill_switch_active)
    await hub.register_device(device_id, ws)
    await hub.broadcast_user(user_id, {"type": "device.online", "device_id": device_id})
    if killed:
        await ws.send_json({"type": "kill_switch", "active": True})
    try:
        await ws.send_json({"type": "hello", "channel": "device", "device_id": device_id})
        while True:
            message = await ws.receive_json()
            msg_type = message.get("type")
            if msg_type == "tool.result":
                payload = message.get("payload") or {}
                hub.resolve_tool(
                    str(message.get("task_id") or payload.get("task_id") or ""),
                    str(message.get("step_id") or payload.get("step_id") or ""),
                    str(message.get("tool") or payload.get("tool") or ""),
                    payload if "success" in payload else message,
                )
            elif msg_type == "heartbeat":
                async with SessionLocal() as db:
                    row = await db.get(Device, device_id)
                    if row and not row.revoked_at:
                        row.last_seen_at = datetime.now(UTC)
                        row.last_heartbeat_at = datetime.now(UTC)
                        row.status = "online"
                        if message.get("platform"):
                            row.platform = str(message["platform"])[:32]
                        if message.get("runtime_version"):
                            row.runtime_version = str(message["runtime_version"])[:32]
                        caps = message.get("capabilities")
                        if isinstance(caps, dict):
                            row.capabilities_json = sanitize_reported_capabilities(row.platform or "windows", caps)
                        voice = message.get("voice")
                        if isinstance(voice, dict):
                            row.voice_json = voice
                        try:
                            await db.commit()
                        except OperationalError:
                            await db.rollback()
                            continue
                        await hub.broadcast_user(
                            user_id,
                            {
                                "type": "device.heartbeat",
                                "device_id": device_id,
                                "last_heartbeat_at": row.last_heartbeat_at.isoformat(),
                                "capabilities": row.capabilities_json,
                            },
                        )
    except WebSocketDisconnect:
        hub.unregister_device(device_id)
        async with SessionLocal() as db:
            row = await db.get(Device, device_id)
            if row:
                row.status = "offline"
                await db.commit()
        await hub.broadcast_user(user_id, {"type": "device.offline", "device_id": device_id})
