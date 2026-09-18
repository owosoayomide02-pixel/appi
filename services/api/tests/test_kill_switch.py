import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("AI_PROVIDER", "heuristic")
os.environ.setdefault("AI_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")

import pytest

from app.database import SessionLocal, init_db
from app.models.enums import TaskStatus
from app.models.tables import Task, User, new_id
from app.security.kill_switch import activate_kill_switch, kill_switch
from app.security.passwords import hash_password


@pytest.mark.asyncio
async def test_kill_switch_cancels_open_tasks():
    await init_db()
    async with SessionLocal() as db:
        user = User(id=new_id(), email="kill@example.com", password_hash=hash_password("correcthorse"))
        db.add(user)
        task = Task(id=new_id(), user_id=user.id, input_text="run forever", status=TaskStatus.RUNNING.value)
        db.add(task)
        await db.commit()
        result = await activate_kill_switch(db, user.id)
        await db.commit()
        assert task.id in result["cancelled_tasks"]
        await db.refresh(task)
        assert task.status == TaskStatus.CANCELLED.value
        assert kill_switch.is_active(user.id)
        kill_switch.clear(user.id)
