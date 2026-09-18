import asyncio

import pytest
from sqlalchemy import select

from app.agents.executor import _execute_step
from app.database import SessionLocal, init_db
from app.models.enums import StepStatus, TaskStatus
from app.models.tables import Device, PermissionRequest, Task, TaskStep, User, new_id
from app.realtime.hub import hub
from app.runtime.capabilities import CAPABILITY_UNAVAILABLE, default_capabilities
from app.security.kill_switch import kill_switch
from app.security.passwords import hash_password


async def _seed(db, *, tool: str, input_json: dict | None = None) -> tuple[User, Device, Task, TaskStep]:
    user = User(id=new_id(), email=f"{new_id()[:8]}@example.com", password_hash=hash_password("correcthorse"))
    device = Device(
        id=new_id(),
        user_id=user.id,
        name="AYOMIDE-LAPTOP",
        os="Windows",
        platform="windows",
        token_hash=new_id(),
        capabilities_json=default_capabilities("windows"),
        runtime_version="0.2.0",
    )
    task = Task(
        id=new_id(),
        user_id=user.id,
        device_id=device.id,
        input_text="test",
        title="test",
        status=TaskStatus.RUNNING.value,
    )
    step = TaskStep(
        id=new_id(),
        task_id=task.id,
        step_key="step_1",
        description=tool,
        tool=tool,
        status=StepStatus.PENDING.value,
        sequence=1,
        input_json=input_json or {},
    )
    db.add_all([user, device, task, step])
    await db.commit()
    await db.refresh(task)
    await db.refresh(step)
    return user, device, task, step


@pytest.mark.asyncio
async def test_blocked_capability_cannot_execute():
    await init_db()
    async with SessionLocal() as db:
        _user, _device, task, step = await _seed(db, tool="payment.execute", input_json={"amount": 25000, "currency": "NGN"})
        outcome = await _execute_step(db, task, step, None)
        assert outcome == "failed"
        err = (step.error or "") + (task.error_message or "")
        assert "CONNECTOR_NOT_CONNECTED" in err or CAPABILITY_UNAVAILABLE in err


@pytest.mark.asyncio
async def test_write_ask_creates_approval_request():
    await init_db()
    async with SessionLocal() as db:
        _user, _device, task, step = await _seed(
            db,
            tool="files.write_file",
            input_json={"path": r"C:\Users\User\Projects\app\a.ts", "content": "export {}\n"},
        )
        running = asyncio.create_task(_execute_step(db, task, step, None))
        request = None
        for _ in range(40):
            await asyncio.sleep(0.05)
            request = (await db.execute(select(PermissionRequest).where(PermissionRequest.step_id == step.id))).scalar_one_or_none()
            if request:
                break
        assert request is not None
        assert request.status == "pending"
        hub.resolve_approval(request.id, "denied")
        outcome = await asyncio.wait_for(running, timeout=5)
        assert outcome == "blocked"


@pytest.mark.asyncio
async def test_allow_read_reaches_runtime_gate():
    await init_db()
    async with SessionLocal() as db:
        _user, _device, task, step = await _seed(
            db,
            tool="files.read_file",
            input_json={"path": r"C:\Users\User\Projects\app\package.json"},
        )
        outcome = await _execute_step(db, task, step, None)
        assert step.approval_required is False
        assert outcome == "failed"
        assert "not connected" in (step.error or "").lower()


@pytest.mark.asyncio
async def test_kill_switch_stops_new_execution():
    await init_db()
    async with SessionLocal() as db:
        user, _device, task, step = await _seed(db, tool="files.read_file")
        kill_switch.arm(user.id)
        try:
            outcome = await _execute_step(db, task, step, None)
            assert outcome == "cancelled"
        finally:
            kill_switch.clear(user.id)
