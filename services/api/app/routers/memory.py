from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.memory.store import retrieve, store_memory
from app.models.enums import MemoryKind
from app.models.tables import Memory, User

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class MemoryIn(BaseModel):
    kind: MemoryKind = MemoryKind.PREFERENCE
    content: str = Field(min_length=1, max_length=4000)
    topic: str = ""
    project_id: str | None = None
    importance: int = 1
    secret_handle: str | None = None


@router.get("")
async def list_memory(
    kind: str | None = None,
    q: str | None = None,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    if q:
        rows = await retrieve(db, user_id=user.id, query=q, project_id=project_id)
    else:
        stmt = select(Memory).where(Memory.user_id == user.id)
        if kind:
            stmt = stmt.where(Memory.kind == kind)
        if project_id:
            stmt = stmt.where(Memory.project_id == project_id)
        rows = (await db.execute(stmt.order_by(Memory.created_at.desc()))).scalars().all()
    out = []
    for row in rows:
        content = row.content
        if row.kind == MemoryKind.SECURE.value:
            content = row.secret_handle or "secret://redacted"
        out.append(
            {
                "id": row.id,
                "kind": row.kind,
                "topic": row.topic,
                "content": content,
                "tool": row.tool,
                "importance": row.importance,
                "project_id": row.project_id,
                "created_at": row.created_at.isoformat(),
            }
        )
    return out


@router.post("")
async def add_memory(payload: MemoryIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    try:
        item = await store_memory(
            db,
            user_id=user.id,
            kind=payload.kind,
            content=payload.content,
            topic=payload.topic,
            project_id=payload.project_id,
            importance=payload.importance,
            secret_handle=payload.secret_handle,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return {"id": item.id}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    row = await db.get(Memory, memory_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}
