from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tables import AuditEvent, User

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
async def list_audit(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=100, le=500),
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(AuditEvent).where(AuditEvent.user_id == user.id).order_by(AuditEvent.timestamp.desc()).limit(limit)
    if task_id:
        stmt = stmt.where(AuditEvent.task_id == task_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "user_id": r.user_id,
            "agent_id": r.agent_id,
            "task_id": r.task_id,
            "step_id": r.step_id,
            "action": r.action,
            "tool": r.tool,
            "target": r.target,
            "risk_level": r.risk_level,
            "permission_decision": r.permission_decision,
            "approved_by": r.approved_by,
            "result": r.result,
            "verification_status": r.verification_status,
        }
        for r in rows
    ]
