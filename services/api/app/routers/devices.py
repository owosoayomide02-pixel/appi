import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.tables import Device, DeviceCapability, Permission, User, new_id
from app.realtime.hub import DeviceOffline, hub
from app.runtime.capabilities import coarse_from_fine, sanitize_reported_capabilities
from app.security.vault import random_token

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

RUNTIME_VERSION = (settings.runtime_version or "0.3.0").strip()


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class PairCompleteIn(BaseModel):
    pairing_code: str = Field(min_length=6, max_length=8)
    name: str = Field(default="Windows Device", max_length=120)
    os: str = Field(default="Windows", max_length=80)
    platform: str | None = None
    runtime_version: str | None = None
    capabilities: dict[str, bool] | None = None


def _normalize_platform(os_name: str, platform: str | None) -> str:
    raw = (platform or os_name or "windows").lower()
    if "win" in raw:
        return "windows"
    if "linux" in raw:
        return "linux"
    if "mac" in raw or "darwin" in raw:
        return "macos"
    if "android" in raw:
        return "android"
    if "ios" in raw or "iphone" in raw:
        return "ios"
    return raw[:32]


def _merged_capabilities(platform: str, reported: dict[str, bool] | None) -> dict[str, bool]:
    return sanitize_reported_capabilities(platform, reported)


def _sync_legacy_caps(cap: DeviceCapability | None, merged: dict[str, bool]) -> None:
    if not cap:
        return
    cap.filesystem = bool(merged.get("filesystem"))
    cap.terminal = bool(merged.get("terminal"))
    cap.browser = bool(merged.get("browser"))
    cap.desktop_ui = bool(merged.get("desktop_ui"))
    cap.microphone = bool(merged.get("microphone"))
    cap.camera = bool(merged.get("camera"))


def serialize_device(device: Device, cap: DeviceCapability | None) -> dict[str, Any]:
    online = hub.device_online(device.id) and device.revoked_at is None
    status = "revoked" if device.revoked_at else ("online" if online else (device.status if device.status != "online" else "offline"))
    caps = device.capabilities_json or {}
    if isinstance(caps, str):
        import json

        caps = json.loads(caps or "{}")
    if not caps and cap:
        caps = {
            "filesystem": cap.filesystem,
            "terminal": cap.terminal,
            "browser": cap.browser,
            "desktop_ui": cap.desktop_ui,
            "microphone": cap.microphone,
            "camera": cap.camera,
        }
    return {
        "id": device.id,
        "name": device.name,
        "os": device.os,
        "platform": device.platform or _normalize_platform(device.os, None),
        "runtime_version": device.runtime_version or RUNTIME_VERSION,
        "status": status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "last_heartbeat_at": device.last_heartbeat_at.isoformat() if device.last_heartbeat_at else None,
        "revoked": bool(device.revoked_at),
        "capabilities": caps,
        "voice": device.voice_json or {},
        "capability_groups": coarse_from_fine(caps) if caps else {
            "filesystem": bool(cap.filesystem) if cap else False,
            "terminal": bool(cap.terminal) if cap else False,
            "browser": bool(cap.browser) if cap else False,
            "desktop_ui": bool(cap.desktop_ui) if cap else False,
            "microphone": bool(cap.microphone) if cap else False,
            "camera": bool(cap.camera) if cap else False,
            "notifications": False,
            "contacts": False,
            "calendar": False,
            "phone_calls": False,
            "payments": False,
        },
    }


@router.post("/pair/start")
async def start_pairing(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    device = Device(
        id=new_id(),
        user_id=user.id,
        name="Pending device",
        os="Windows",
        platform="windows",
        status="pairing",
        token_hash=_hash(random_token()),
        pairing_code_hash=_hash(code),
        pairing_expires_at=datetime.now(UTC) + timedelta(minutes=15),
        runtime_version=RUNTIME_VERSION,
        capabilities_json={},
    )
    db.add(device)
    db.add(
        DeviceCapability(
            id=new_id(),
            device_id=device.id,
            filesystem=True,
            terminal=True,
            browser=True,
        )
    )
    await db.commit()
    return {"device_id": device.id, "pairing_code": code, "expires_at": device.pairing_expires_at.isoformat()}


@router.post("/pair/complete")
async def complete_pairing(payload: PairCompleteIn, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    code_hash = _hash(payload.pairing_code.strip())
    device = (await db.execute(select(Device).where(Device.pairing_code_hash == code_hash))).scalar_one_or_none()
    if not device or not device.pairing_expires_at:
        raise HTTPException(status_code=400, detail="Invalid pairing code")
    expires = device.pairing_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Pairing code expired")
    platform = _normalize_platform(payload.os, payload.platform)
    merged = _merged_capabilities(platform, payload.capabilities)
    token = random_token(32)
    device.token_hash = _hash(token)
    device.name = payload.name
    device.os = payload.os
    device.platform = platform
    device.runtime_version = payload.runtime_version or RUNTIME_VERSION
    device.capabilities_json = merged
    device.status = "offline"
    device.pairing_code_hash = None
    device.pairing_expires_at = None
    cap = (await db.execute(select(DeviceCapability).where(DeviceCapability.device_id == device.id))).scalar_one_or_none()
    _sync_legacy_caps(cap, merged)
    await db.commit()
    owner = await db.get(User, device.user_id)
    return {
        "device_id": device.id,
        "device_token": token,
        "user_id": device.user_id,
        "platform": platform,
        "display_name": (owner.display_name if owner else "") or "",
    }


@router.get("")
async def list_devices(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    devices = (await db.execute(select(Device).where(Device.user_id == user.id))).scalars().all()
    out = []
    for device in devices:
        cap = (await db.execute(select(DeviceCapability).where(DeviceCapability.device_id == device.id))).scalar_one_or_none()
        out.append(serialize_device(device, cap))
    return out


@router.get("/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    device = await db.get(Device, device_id)
    if not device or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    cap = (await db.execute(select(DeviceCapability).where(DeviceCapability.device_id == device.id))).scalar_one_or_none()
    grants = (
        await db.execute(
            select(Permission).where(Permission.user_id == user.id, Permission.revoked_at.is_(None))
        )
    ).scalars().all()
    payload = serialize_device(device, cap)
    payload["granted_permissions"] = [
        {
            "id": g.id,
            "resource": g.resource,
            "scope": g.scope,
            "actions": g.actions,
            "kind": g.kind,
            "expires_at": g.expires_at.isoformat() if g.expires_at else None,
        }
        for g in grants
        if g.kind in {"one_time", "session", "time_limited", "permanent"}
    ]
    payload["temporary_permissions"] = [p for p in payload["granted_permissions"] if p["kind"] != "permanent"]
    return payload


class VoicePrefsIn(BaseModel):
    tts_voice: str = ""
    tts_gender: str = ""
    culture: str = ""
    min_confidence: float | None = None


@router.patch("/{device_id}/voice")
async def update_device_voice(
    device_id: str,
    payload: VoicePrefsIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    device = await db.get(Device, device_id)
    if not device or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    current = dict(device.voice_json or {})
    current["tts_voice"] = payload.tts_voice
    current["tts_gender"] = payload.tts_gender
    current["culture"] = payload.culture
    if payload.min_confidence is not None:
        current["min_confidence"] = payload.min_confidence
    device.voice_json = current
    await db.commit()
    applied = False
    try:
        await hub.send_device(
            device.id,
            {
                "type": "voice.prefs",
                "tts_voice": payload.tts_voice,
                "tts_gender": payload.tts_gender,
                "culture": payload.culture,
                "min_confidence": payload.min_confidence,
            },
        )
        applied = True
    except DeviceOffline:
        applied = False
    return {"ok": True, "applied": applied, "voice": current}


@router.post("/{device_id}/revoke")
async def revoke_device(device_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    device = await db.get(Device, device_id)
    if not device or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    device.revoked_at = datetime.now(UTC)
    device.status = "revoked"
    device.token_hash = _hash(random_token())
    await db.commit()
    await hub.disconnect_device(device.id)
    return {"status": "revoked"}
