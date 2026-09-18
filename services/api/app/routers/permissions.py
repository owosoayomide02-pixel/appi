from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.executor import spawn_task
from app.audit.logger import log_event
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import PermissionKind, PermissionRequestStatus, TaskStatus
from app.models.tables import Permission, PermissionRequest, Task, User, UserPolicy, new_id
from app.permissions.path_guard import PathNotAllowed, validate_allowed_folder
from app.realtime.hub import hub
from app.state.machine import transition

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


class PolicyUpdate(BaseModel):
    read_project_files: str | None = None
    edit_project_files: str | None = None
    run_tests: str | None = None
    run_terminal: str | None = None
    use_browser: str | None = None
    delete_files: str | None = None


class PermissionCreate(BaseModel):
    subject: str
    resource: str
    scope: str
    actions: list[str]
    kind: str = PermissionKind.SESSION.value
    expires_minutes: int | None = 60
    requires_confirmation: bool = False


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved_once|approved_task|approved_similar|denied)$")


class FolderIn(BaseModel):
    path: str
    device_id: str | None = None


@router.get("/policy")
async def get_policy(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    policy = (await db.execute(select(UserPolicy).where(UserPolicy.user_id == user.id))).scalar_one_or_none()
    if not policy:
        policy = UserPolicy(id=new_id(), user_id=user.id)
        db.add(policy)
        await db.commit()
    return {
        "read_project_files": policy.read_project_files,
        "edit_project_files": policy.edit_project_files,
        "run_tests": policy.run_tests,
        "run_terminal": policy.run_terminal,
        "use_browser": policy.use_browser,
        "delete_files": policy.delete_files,
    }


@router.put("/policy")
async def update_policy(payload: PolicyUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    policy = (await db.execute(select(UserPolicy).where(UserPolicy.user_id == user.id))).scalar_one_or_none()
    if not policy:
        policy = UserPolicy(id=new_id(), user_id=user.id)
        db.add(policy)
    for field, value in payload.model_dump(exclude_none=True).items():
        if value not in {"ALLOW", "ASK", "BLOCK"}:
            raise HTTPException(status_code=400, detail=f"Invalid decision for {field}")
        setattr(policy, field, value)
    await db.commit()
    return await get_policy(db, user)


@router.get("")
async def list_permissions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = (await db.execute(select(Permission).where(Permission.user_id == user.id, Permission.revoked_at.is_(None)))).scalars().all()
    return [
        {
            "id": r.id,
            "subject": r.subject,
            "resource": r.resource,
            "scope": r.scope,
            "actions": r.actions,
            "kind": r.kind,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "requires_confirmation": r.requires_confirmation,
        }
        for r in rows
    ]


@router.post("")
async def create_permission(payload: PermissionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    expires = datetime.now(UTC) + timedelta(minutes=payload.expires_minutes) if payload.expires_minutes else None
    if payload.kind == PermissionKind.PERMANENT.value:
        expires = None
    row = Permission(
        id=new_id(),
        user_id=user.id,
        subject=payload.subject,
        resource=payload.resource,
        scope=payload.scope,
        actions=payload.actions,
        kind=payload.kind,
        expires_at=expires,
        requires_confirmation=payload.requires_confirmation,
    )
    db.add(row)
    await db.commit()
    return {"id": row.id}


@router.post("/{permission_id}/revoke")
async def revoke_permission(permission_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    row = await db.get(Permission, permission_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Permission not found")
    row.revoked_at = datetime.now(UTC)
    await db.commit()
    return {"status": "revoked"}


@router.get("/requests")
async def list_requests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(PermissionRequest).where(PermissionRequest.user_id == user.id).order_by(PermissionRequest.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "action": r.action,
            "tool": r.tool,
            "target": r.target,
            "command": r.command,
            "risk": r.risk,
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "metadata": r.metadata_json or {},
        }
        for r in rows
    ]


@router.post("/requests/{request_id}/decide")
async def decide_request(
    request_id: str,
    payload: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    req = await db.get(PermissionRequest, request_id)
    if not req or req.user_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != PermissionRequestStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Request already decided")
    req.status = payload.decision
    req.decided_at = datetime.now(UTC)
    req.decided_by = user.id
    if payload.decision in {
        PermissionRequestStatus.APPROVED_ONCE.value,
        PermissionRequestStatus.APPROVED_TASK.value,
        PermissionRequestStatus.APPROVED_SIMILAR.value,
    } and req.task_id:
        expires = datetime.now(UTC) + timedelta(hours=4)
        kind = PermissionKind.ONE_TIME.value if payload.decision == PermissionRequestStatus.APPROVED_ONCE.value else PermissionKind.SESSION.value
        db.add(
            Permission(
                id=new_id(),
                user_id=user.id,
                subject=f"task_{req.task_id}",
                resource=req.tool.split(".")[0],
                scope=req.target or "*",
                actions=[req.tool.split(".")[-1], "*"],
                kind=kind,
                expires_at=expires,
                task_id=req.task_id,
            )
        )
        task = await db.get(Task, req.task_id)
        if task and task.status == TaskStatus.WAITING_FOR_APPROVAL.value:
            task.status = transition(task.status, TaskStatus.RUNNING).value
    await log_event(
        db,
        user_id=user.id,
        task_id=req.task_id,
        step_id=req.step_id,
        action="permission.decided",
        tool=req.tool,
        target=req.target,
        risk_level=req.risk,
        permission_decision="ALLOW" if payload.decision != "denied" else "BLOCK",
        approved_by=user.id,
        result=payload.decision,
    )
    await db.commit()
    hub.resolve_approval(request_id, payload.decision)
    return {"status": payload.decision}
