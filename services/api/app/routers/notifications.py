from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tables import Notification, User

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(80)
        )
    ).scalars().all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "read": n.read,
            "task_id": n.task_id,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    row = await db.get(Notification, notification_id)
    if row and row.user_id == user.id:
        row.read = True
        await db.commit()
    return {"status": "ok"}
