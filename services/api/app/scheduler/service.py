"""Scheduled jobs. Guardian still runs at execution time."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.executor import spawn_task
from app.models.enums import TaskStatus
from app.models.tables import ScheduledJob, Task, new_id


async def enqueue_due_jobs(db: AsyncSession) -> int:
    now = datetime.now(UTC)
    rows = (await db.execute(select(ScheduledJob).where(ScheduledJob.enabled.is_(True), ScheduledJob.next_run_at <= now))).scalars().all()
    count = 0
    for job in rows:
        if job.expires_at and job.expires_at <= now:
            job.enabled = False
            continue
        task = Task(
            id=new_id(),
            user_id=job.user_id,
            device_id=job.device_id,
            project_id=job.project_id,
            input_text=job.input_text,
            title=f"Scheduled: {job.input_text.strip()[:160]}",
            status=TaskStatus.CREATED.value,
        )
        db.add(task)
        await db.commit()
        spawn_task(task.id)
        job.last_run_at = now
        job.retry_count = 0
        if job.interval_seconds and job.interval_seconds > 0:
            job.next_run_at = now + timedelta(seconds=job.interval_seconds)
        else:
            job.enabled = False
        count += 1
    if rows:
        await db.commit()
    return count
