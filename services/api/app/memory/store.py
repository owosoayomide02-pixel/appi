from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MemoryKind
from app.models.tables import Memory, new_id
from app.security.vault import is_handle

MAX_RETRIEVAL = 8


def _tokenize(text: str) -> set[str]:
    return {part.lower() for part in text.replace("/", " ").replace("_", " ").split() if len(part) > 2}


async def store_memory(
    db: AsyncSession,
    *,
    user_id: str,
    kind: MemoryKind,
    content: str,
    topic: str = "",
    tool: str | None = None,
    project_id: str | None = None,
    task_id: str | None = None,
    importance: int = 1,
    secret_handle: str | None = None,
    ttl_minutes: int | None = None,
) -> Memory:
    if kind == MemoryKind.SECURE:
        if content and not is_handle(content) and not secret_handle:
            raise ValueError("Secure memory must store a handle, not a raw secret")
        content = secret_handle or content
    expires = datetime.now(UTC) + timedelta(minutes=ttl_minutes) if ttl_minutes else None
    if kind == MemoryKind.WORKING and ttl_minutes is None:
        expires = datetime.now(UTC) + timedelta(hours=6)
    item = Memory(
        id=new_id(),
        user_id=user_id,
        kind=kind.value,
        project_id=project_id,
        task_id=task_id,
        topic=topic,
        tool=tool,
        importance=importance,
        content=content,
        secret_handle=secret_handle,
        expires_at=expires,
    )
    db.add(item)
    await db.flush()
    return item


async def summarize_working_memory(db: AsyncSession, user_id: str, task_id: str) -> None:
    rows = (
        await db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.task_id == task_id,
                Memory.kind == MemoryKind.WORKING.value,
            )
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for row in rows:
        row.expires_at = now


async def retrieve(
    db: AsyncSession,
    *,
    user_id: str,
    query: str,
    project_id: str | None = None,
    tool: str | None = None,
    limit: int = MAX_RETRIEVAL,
) -> list[Memory]:
    now = datetime.now(UTC)
    stmt = select(Memory).where(
        Memory.user_id == user_id,
        or_(Memory.expires_at.is_(None), Memory.expires_at > now),
        Memory.kind != MemoryKind.SECURE.value,
    )
    if project_id:
        stmt = stmt.where(or_(Memory.project_id == project_id, Memory.project_id.is_(None)))
    rows = (await db.execute(stmt)).scalars().all()
    tokens = _tokenize(query)
    scored: list[tuple[float, Memory]] = []
    for row in rows:
        score = float(row.importance)
        haystack = _tokenize(f"{row.topic} {row.content} {row.tool or ''}")
        score += 3 * len(tokens & haystack)
        if tool and row.tool == tool:
            score += 2
        if project_id and row.project_id == project_id:
            score += 2
        created = row.created_at
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        age_hours = max((now - created).total_seconds() / 3600, 0.1) if created else 1.0
        score += 1 / age_hours
        if score > 1:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]
