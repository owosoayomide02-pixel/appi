from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.redaction import redact_text, redact_value
from app.models.tables import AuditEvent, new_id


async def log_event(
    db: AsyncSession,
    *,
    user_id: str,
    action: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    step_id: str | None = None,
    tool: str | None = None,
    target: str | None = None,
    risk_level: str = "low",
    permission_decision: str | None = None,
    approved_by: str | None = None,
    result: str | None = None,
    verification_status: str | None = None,
    extra: dict | None = None,
    commit: bool = False,
) -> AuditEvent:
    event = AuditEvent(
        id=new_id(),
        timestamp=datetime.now(UTC),
        user_id=user_id,
        agent_id=agent_id,
        task_id=task_id,
        step_id=step_id,
        action=action,
        tool=tool,
        target=redact_text(target) if target else None,
        risk_level=risk_level,
        permission_decision=permission_decision,
        approved_by=approved_by,
        result=result,
        verification_status=verification_status,
        extra=redact_value(extra) if extra else None,
    )
    db.add(event)
    if commit:
        await db.commit()
        await db.refresh(event)
    else:
        await db.flush()
    return event
