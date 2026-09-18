from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.audit.logger import log_event
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import NotificationType
from app.models.tables import Device, Notification, PermissionRequest, User, new_id
from app.realtime.hub import hub
from app.security.kill_switch import activate_kill_switch, deactivate_kill_switch, kill_switch

router = APIRouter(prefix="/api/v1/kill-switch", tags=["kill-switch"])


@router.post("/stop")
async def stop_appi(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    result = await activate_kill_switch(db, user.id)
    pending = (
        await db.execute(
            select(PermissionRequest).where(
                PermissionRequest.user_id == user.id,
                PermissionRequest.status == "pending",
            )
        )
    ).scalars().all()
    for req in pending:
        hub.resolve_approval(req.id, "denied")
    await log_event(
        db,
        user_id=user.id,
        action="kill_switch.activated",
        risk_level="high",
        result="SUCCESS",
        commit=False,
    )
    await hub.broadcast_user(
        user.id,
        {"type": "kill_switch", "active": True, "message": "STOP APPI triggered. All actions halted."},
    )
    devices = (await db.execute(select(Device).where(Device.user_id == user.id))).scalars().all()
    for device in devices:
        if hub.device_online(device.id):
            try:
                await hub.send_device(device.id, {"type": "kill_switch", "active": True})
            except Exception:
                pass
            await hub.disconnect_device(device.id)
    db.add(
        Notification(
            id=new_id(),
            user_id=user.id,
            type=NotificationType.KILL_SWITCH.value,
            title="STOP APPI",
            body="All running tasks were cancelled and temporary permissions revoked.",
        )
    )
    await db.commit()
    return {"active": True, **result}


@router.post("/resume")
async def resume_appi(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    await deactivate_kill_switch(db, user.id)
    await log_event(db, user_id=user.id, action="kill_switch.cleared", result="SUCCESS", commit=True)
    await hub.broadcast_user(user.id, {"type": "kill_switch", "active": False})
    return {"active": False}


@router.get("")
async def status(user: User = Depends(get_current_user)) -> dict:
    return {"active": kill_switch.is_active(user.id) or user.kill_switch_active}
