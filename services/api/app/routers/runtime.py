from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.executor import spawn_task
from app.database import get_db
from app.models.enums import TaskStatus
from app.models.tables import Device, ScheduledJob, Task, User, new_id
from app.resolver.action import resolve_action
from app.runtime.capabilities import CAPABILITIES, GROUP_FLAGS, default_capabilities
from app.security.kill_switch import kill_switch

router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


async def _device_from_token(db: AsyncSession, token: str) -> Device:
    device = (await db.execute(select(Device).where(Device.token_hash == _hash(token)))).scalar_one_or_none()
    if not device or device.revoked_at:
        raise HTTPException(status_code=401, detail="Invalid device token")
    return device


@router.get("/capabilities")
async def list_capabilities() -> dict:
    return {
        "groups": list(GROUP_FLAGS),
        "capabilities": [
            {"id": name, **meta, "implemented": bool(meta.get("implemented_on"))}
            for name, meta in CAPABILITIES.items()
        ],
        "profiles": {
            platform: default_capabilities(platform)
            for platform in ("windows", "linux", "macos", "android", "ios")
        },
    }


class VoiceCommandIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    source: str = "voice"


@router.post("/voice-command")
async def voice_command(
    payload: VoiceCommandIn,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    device = await _device_from_token(db, token)
    user = await db.get(User, device.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")
    if kill_switch.is_active(user.id) or user.kill_switch_active:
        raise HTTPException(status_code=423, detail="Kill switch is active")
    spoken = payload.text.strip()
    stored = spoken if spoken.lower().startswith("[voice]") else f"[voice] {spoken}"
    task = Task(
        id=new_id(),
        user_id=user.id,
        device_id=device.id,
        input_text=stored,
        title=spoken[:180],
        status=TaskStatus.CREATED.value,
    )
    db.add(task)
    await db.commit()
    spawn_task(task.id)
    task = (await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task.id))).scalar_one()
    resolved = resolve_action(spoken)
    return {
        "id": task.id,
        "status": task.status,
        "title": task.title,
        "resolver": {
            "intent": resolved.intent,
            "service": resolved.service,
            "risk": resolved.risk,
            "connector_available": resolved.connector_available,
            "path": resolved.path,
            "permission": resolved.permission,
        },
    }


@router.get("/whoami")
async def runtime_whoami(token: str = Query(...), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    device = await _device_from_token(db, token)
    user = await db.get(User, device.user_id)
    return {
        "device_id": device.id,
        "user_id": device.user_id,
        "display_name": (user.display_name if user else "") or "",
    }


@router.get("/voice-prefs")
async def runtime_voice_prefs(token: str = Query(...), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    device = await _device_from_token(db, token)
    return dict(device.voice_json or {})


@router.get("/task/{task_id}")
async def runtime_task(task_id: str, token: str = Query(...), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    device = await _device_from_token(db, token)
    task = (
        await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task_id, Task.user_id == device.user_id))
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "status": task.status,
        "result_summary": task.result_summary,
        "error_message": task.error_message,
        "verified": task.verified,
        "steps": [{"tool": s.tool, "status": s.status, "error": s.error} for s in task.steps],
    }


class ScheduleIn(BaseModel):
    input_text: str = Field(min_length=1, max_length=8000)
    next_run_at: str
    interval_seconds: int | None = None
    timezone: str = "UTC"
    device_id: str | None = None
    project_id: str | None = None


@router.post("/schedule")
async def create_schedule(payload: ScheduleIn, token: str = Query(...), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    from datetime import datetime

    device = await _device_from_token(db, token)
    job = ScheduledJob(
        id=new_id(),
        user_id=device.user_id,
        device_id=payload.device_id or device.id,
        project_id=payload.project_id,
        input_text=payload.input_text,
        timezone=payload.timezone,
        interval_seconds=payload.interval_seconds,
        next_run_at=datetime.fromisoformat(payload.next_run_at.replace("Z", "+00:00")),
    )
    db.add(job)
    await db.commit()
    return {"id": job.id, "next_run_at": job.next_run_at.isoformat(), "enabled": job.enabled}
