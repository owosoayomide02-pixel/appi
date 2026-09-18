from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tables import Task, TaskStep, User

router = APIRouter(prefix="/api/v1/diffs", tags=["diffs"])


@router.get("/{task_id}")
async def task_diffs(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    task = await db.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    steps = (
        await db.execute(select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.tool.in_(["files.write_file", "files.create_file"])))
    ).scalars().all()
    diffs = []
    for step in steps:
        data = (step.output_json or {}).get("data") or {}
        diffs.append(
            {
                "step_id": step.id,
                "path": (step.input_json or {}).get("path") or data.get("path"),
                "before": data.get("before") or "",
                "after": data.get("after") or data.get("content") or (step.input_json or {}).get("content") or "",
                "status": step.status,
            }
        )
    return diffs
