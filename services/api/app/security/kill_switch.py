"""Kill switch operates below the AI layer. The model cannot veto it."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PermissionKind, TaskStatus
from app.models.tables import AgentSession, Permission, Task, User
from app.state.machine import transition


class KillSwitch:
    def __init__(self) -> None:
        self._users: set[str] = set()
        self._lock = Lock()

    def is_active(self, user_id: str) -> bool:
        with self._lock:
            return user_id in self._users

    def arm(self, user_id: str) -> None:
        with self._lock:
            self._users.add(user_id)

    def clear(self, user_id: str) -> None:
        with self._lock:
            self._users.discard(user_id)


kill_switch = KillSwitch()


async def activate_kill_switch(db: AsyncSession, user_id: str) -> dict:
    kill_switch.arm(user_id)
    now = datetime.now(UTC)

    user = await db.get(User, user_id)
    if user:
        user.kill_switch_active = True

    sessions = (await db.execute(select(AgentSession).where(AgentSession.user_id == user_id, AgentSession.status == "active"))).scalars().all()
    for session in sessions:
        session.kill_switch_active = True
        session.status = "killed"
        session.ended_at = now

    tasks = (
        await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status.in_(
                    [
                        TaskStatus.CREATED.value,
                        TaskStatus.PLANNING.value,
                        TaskStatus.WAITING_FOR_APPROVAL.value,
                        TaskStatus.RUNNING.value,
                        TaskStatus.VERIFYING.value,
                    ]
                ),
            )
        )
    ).scalars().all()
    cancelled: list[str] = []
    for task in tasks:
        task.status = transition(task.status, TaskStatus.CANCELLED).value
        task.error_message = "Cancelled by kill switch"
        task.completed_at = now
        cancelled.append(task.id)

    await db.execute(
        update(Permission)
        .where(
            Permission.user_id == user_id,
            Permission.revoked_at.is_(None),
            Permission.kind.in_(
                [
                    PermissionKind.ONE_TIME.value,
                    PermissionKind.SESSION.value,
                    PermissionKind.TIME_LIMITED.value,
                    PermissionKind.AMOUNT_LIMITED.value,
                ]
            ),
        )
        .values(revoked_at=now)
    )
    await db.flush()
    return {"cancelled_tasks": cancelled, "sessions_killed": len(sessions)}


async def deactivate_kill_switch(db: AsyncSession, user_id: str) -> None:
    kill_switch.clear(user_id)
    user = await db.get(User, user_id)
    if user:
        user.kill_switch_active = False
        await db.commit()
