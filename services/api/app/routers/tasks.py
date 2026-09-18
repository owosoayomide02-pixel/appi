from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.executor import spawn_task
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import TaskStatus
from app.models.tables import Device, Project, Task, TaskStep, User, new_id
from app.security.kill_switch import kill_switch

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    input_text: str = Field(min_length=1, max_length=8000)
    project_id: str | None = None
    device_id: str | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    goal: str
    input_text: str
    status: str
    result_summary: str | None
    error_message: str | None
    verified: bool
    project_id: str | None
    device_id: str | None
    created_at: str
    steps: list[dict[str, Any]] = []


def _task_out(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "goal": task.goal,
        "input_text": task.input_text,
        "status": task.status,
        "result_summary": task.result_summary,
        "error_message": task.error_message,
        "verified": task.verified,
        "project_id": task.project_id,
        "device_id": task.device_id,
        "created_at": task.created_at.isoformat(),
        "steps": [
            {
                "id": s.id,
                "step_key": s.step_key,
                "description": s.description,
                "tool": s.tool,
                "risk": s.risk,
                "status": s.status,
                "depends_on": s.depends_on,
                "approval_required": s.approval_required,
                "sequence": s.sequence,
                "error": s.error,
                "output": s.output_json,
            }
            for s in sorted(task.steps, key=lambda x: x.sequence)
        ],
    }


@router.post("", status_code=201)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if kill_switch.is_active(user.id) or user.kill_switch_active:
        raise HTTPException(status_code=423, detail="Kill switch is active. Resume Appi in Device settings to continue.")
    device_id = payload.device_id
    if not device_id:
        device = (await db.execute(select(Device).where(Device.user_id == user.id))).scalars().first()
        device_id = device.id if device else None
    if payload.project_id:
        project = await db.get(Project, payload.project_id)
        if not project or project.user_id != user.id:
            raise HTTPException(status_code=404, detail="Project not found")
    task = Task(
        id=new_id(),
        user_id=user.id,
        device_id=device_id,
        project_id=payload.project_id,
        input_text=payload.input_text.strip(),
        title=payload.input_text.strip()[:180],
        status=TaskStatus.CREATED.value,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    spawn_task(task.id)
    task = (
        await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task.id))
    ).scalar_one()
    return _task_out(task)


@router.get("")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    active: bool | None = None,
) -> list[dict[str, Any]]:
    stmt = select(Task).options(selectinload(Task.steps)).where(Task.user_id == user.id).order_by(Task.created_at.desc())
    tasks = (await db.execute(stmt)).scalars().all()
    if active:
        live = {
            TaskStatus.CREATED.value,
            TaskStatus.PLANNING.value,
            TaskStatus.WAITING_FOR_APPROVAL.value,
            TaskStatus.RUNNING.value,
            TaskStatus.VERIFYING.value,
        }
        tasks = [t for t in tasks if t.status in live]
    return [_task_out(t) for t in tasks]


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    task = (
        await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task_id, Task.user_id == user.id))
    ).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_out(task)
