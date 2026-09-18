from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.recovery import MAX_REPLANS, MAX_RETRIES, classify_error
from app.audit.logger import log_event
from app.audit.redaction import redact_value
from app.database import SessionLocal
from app.memory.store import retrieve, store_memory, summarize_working_memory
from app.models.enums import (
    ConnectionStatus,
    MemoryKind,
    NotificationType,
    PermissionDecision,
    PermissionKind,
    PermissionRequestStatus,
    StepStatus,
    TaskStatus,
)
from app.models.tables import (
    AllowedFolder,
    Connection,
    Device,
    DeviceCapability,
    DomainPermission,
    Notification,
    Permission,
    PermissionRequest,
    Project,
    Task,
    TaskStep,
    ToolCall,
    User,
    UserPolicy,
    new_id,
)
from app.guardian.engine import GuardianContext, guard
from app.integrations.gmail import (
    gmail_draft,
    gmail_list,
    gmail_read,
    gmail_send,
    load_stored_gmail_token,
)
from app.integrations.google_calendar import calendar_create, calendar_list, load_stored_calendar_token
from app.integrations.github import github_list_repos, github_whoami, load_stored_token
from app.permissions.engine import domain_from_url
from app.runtime.capabilities import CAPABILITY_UNAVAILABLE, capability_for_tool, default_capabilities
from app.providers.factory import get_provider
from app.realtime.hub import DeviceOffline, hub
from app.security.injection import SYSTEM_RULES, wrap_tool_output, wrap_untrusted, wrap_user
from app.security.kill_switch import kill_switch
from app.security.terminal import TerminalDenied, validate_command
from app.state.machine import InvalidStateTransition, mark_completed, transition
from app.tools.protocol import ToolRequest
from app.tools.registry import get_tool, load_default_tools
from app.verification.engine import verify_tool

load_default_tools()

EXECUTE_ALIASES = {
    "filesystem.read": "files.read_file",
    "filesystem.write": "files.write_file",
    "filesystem.delete": "files.delete_file",
    "terminal.execute": "terminal.run_command",
    "process.start": "terminal.start_process",
    "process.stop": "terminal.stop_process",
    "browser.navigate": "browser.open_url",
    "browser.read": "browser.read_page",
    "browser.upload": "browser.upload_file",
    "browser.download": "browser.download_file",
    "browser.search": "browser.open_url",
    "desktop.launch_app": "app.launch",
}


PAYMENT_PROVIDERS = {"paystack", "stripe", "open_banking"}


async def _payment_connector_connected(db: AsyncSession, user_id: str) -> bool:
    row = (
        await db.execute(
            select(Connection).where(
                Connection.user_id == user_id,
                Connection.provider.in_(tuple(PAYMENT_PROVIDERS)),
                Connection.status == ConnectionStatus.CONNECTED.value,
            )
        )
    ).scalars().first()
    return row is not None


async def _device_caps(db: AsyncSession, device_id: str | None) -> tuple[str, dict | None]:
    if not device_id:
        return "windows", None
    device = await db.get(Device, device_id)
    if not device:
        return "windows", None
    platform = device.platform or "windows"
    raw_caps = device.capabilities_json or {}
    if isinstance(raw_caps, str):
        import json

        raw_caps = json.loads(raw_caps or "{}")
    caps = dict(raw_caps or {})
    if device.revoked_at:
        return platform, {}
    if not caps:
        cap = (await db.execute(select(DeviceCapability).where(DeviceCapability.device_id == device.id))).scalar_one_or_none()
        caps = default_capabilities(platform)
        if cap:
            caps["filesystem"] = cap.filesystem
            caps["terminal"] = cap.terminal
            caps["browser"] = cap.browser
            caps["desktop_ui"] = cap.desktop_ui
            caps["microphone"] = cap.microphone
            caps["camera"] = cap.camera
    return platform, caps


def _set_status(task: Task, target: TaskStatus) -> None:
    task.status = transition(task.status, target).value
    task.updated_at = datetime.now(UTC)


async def _notify(db: AsyncSession, user_id: str, ntype: NotificationType, title: str, body: str, task_id: str | None = None) -> None:
    db.add(
        Notification(
            id=new_id(),
            user_id=user_id,
            type=ntype.value,
            title=title,
            body=body,
            task_id=task_id,
        )
    )
    await hub.broadcast_user(
        user_id,
        {"type": "notification", "notification_type": ntype.value, "title": title, "body": body, "task_id": task_id},
    )


async def _policy_map(db: AsyncSession, user_id: str) -> dict[str, str]:
    policy = (await db.execute(select(UserPolicy).where(UserPolicy.user_id == user_id))).scalar_one_or_none()
    if not policy:
        return {}
    return {
        "read_project_files": policy.read_project_files,
        "edit_project_files": policy.edit_project_files,
        "run_tests": policy.run_tests,
        "run_terminal": policy.run_terminal,
        "use_browser": policy.use_browser,
        "delete_files": policy.delete_files,
    }


async def _grants(db: AsyncSession, user_id: str, task_id: str | None) -> list[dict]:
    rows = (
        await db.execute(
            select(Permission).where(Permission.user_id == user_id, Permission.revoked_at.is_(None))
        )
    ).scalars().all()
    out = []
    for row in rows:
        if row.task_id and task_id and row.task_id != task_id and row.kind == PermissionKind.ONE_TIME.value:
            continue
        out.append(
            {
                "resource": row.resource,
                "scope": row.scope,
                "actions": row.actions,
                "expires_at": row.expires_at,
                "requires_confirmation": row.requires_confirmation,
                "revoked_at": row.revoked_at,
                "kind": row.kind,
                "task_id": row.task_id,
            }
        )
    return out


async def persist_plan(db: AsyncSession, task: Task, plan) -> None:
    task.goal = plan.goal
    task.title = plan.goal[:180]
    existing = (
        await db.execute(select(TaskStep).where(TaskStep.task_id == task.id))
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    await db.flush()
    for index, step in enumerate(plan.steps, start=1):
        db.add(
            TaskStep(
                id=new_id(),
                task_id=task.id,
                step_key=step.id,
                description=step.description,
                tool=step.tool,
                risk=step.risk,
                status=StepStatus.PENDING.value,
                depends_on=step.depends_on,
                approval_required=step.approval_required,
                sequence=index,
                input_json=step.input,
            )
        )


async def run_task(task_id: str) -> None:
    async with SessionLocal() as db:
        try:
            await _run_task(db, task_id)
        except Exception as exc:
            task = await db.get(Task, task_id)
            if task and task.status not in {TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value, TaskStatus.BLOCKED.value}:
                try:
                    _set_status(task, TaskStatus.FAILED)
                except InvalidStateTransition:
                    task.status = TaskStatus.FAILED.value
                task.error_message = str(exc)
                await db.commit()
                await hub.broadcast_user(task.user_id, {"type": "task.updated", "task_id": task.id, "status": task.status})


async def _run_task(db: AsyncSession, task_id: str) -> None:
    task = (
        await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task_id))
    ).scalar_one()
    if kill_switch.is_active(task.user_id):
        _set_status(task, TaskStatus.CANCELLED)
        task.error_message = "Kill switch is active"
        await db.commit()
        return

    provider = get_provider()
    project = await db.get(Project, task.project_id) if task.project_id else None
    memories = await retrieve(db, user_id=task.user_id, query=task.input_text, project_id=task.project_id)
    memory_blob = "\n".join(f"- [{m.kind}] {m.topic}: {m.content}" for m in memories)
    context = (
        f"{wrap_user(task.input_text)}\n"
        f"Project path: {project.root_path if project else ''}\n"
        f"Relevant memory:\n{memory_blob}\n"
        f"{SYSTEM_RULES}"
    )

    _set_status(task, TaskStatus.PLANNING)
    task.started_at = datetime.now(UTC)
    await db.commit()
    await hub.broadcast_user(task.user_id, {"type": "task.updated", "task_id": task.id, "status": task.status})

    task.model_calls_used += 1
    plan = await provider.plan(task.input_text, context=context)
    await persist_plan(db, task, plan)
    await log_event(db, user_id=task.user_id, task_id=task.id, action="plan.created", extra={"goal": plan.goal, "steps": len(plan.steps)})
    await db.commit()
    db.expire(task, ["steps"])
    await hub.broadcast_user(task.user_id, {"type": "task.planned", "task_id": task.id, "goal": plan.goal})

    replans = 0
    while True:
        if kill_switch.is_active(task.user_id):
            _set_status(task, TaskStatus.CANCELLED)
            task.error_message = "Cancelled by kill switch"
            await db.commit()
            return
        if task.tool_calls_used >= task.budget_max_tool_calls or task.model_calls_used >= task.budget_max_model_calls:
            _set_status(task, TaskStatus.FAILED)
            task.error_message = "Task budget exhausted"
            await db.commit()
            await _notify(db, task.user_id, NotificationType.TASK_FAILED, "Task budget exhausted", task.error_message, task.id)
            await db.commit()
            return

        db.expire(task, ["steps"])
        task = (
            await db.execute(select(Task).options(selectinload(Task.steps)).where(Task.id == task_id))
        ).scalar_one()
        pending = [s for s in sorted(task.steps, key=lambda s: s.sequence) if s.status == StepStatus.PENDING.value]
        if not pending:
            if not task.steps:
                _set_status(task, TaskStatus.FAILED)
                task.error_message = "Planner produced no executable steps"
                await db.commit()
                return
            await _finalize(db, task, provider)
            return

        step = pending[0]
        outcome = await _execute_step(db, task, step, project)
        if outcome == "waiting":
            return
        if outcome == "blocked":
            _set_status(task, TaskStatus.BLOCKED)
            await db.commit()
            await hub.broadcast_user(task.user_id, {"type": "task.updated", "task_id": task.id, "status": task.status})
            return
        if outcome == "cancelled":
            _set_status(task, TaskStatus.CANCELLED)
            await db.commit()
            return
        if outcome == "failed":
            classification = classify_error(step.error or "")
            if classification == "retry" and task.retry_count < MAX_RETRIES:
                task.retry_count += 1
                step.status = StepStatus.PENDING.value
                step.error = None
                _set_status(task, TaskStatus.RUNNING)
                await db.commit()
                continue
            if classification == "replan" and replans < MAX_REPLANS:
                replans += 1
                observation = wrap_tool_output(step.tool, step.error or "step failed")
                task.model_calls_used += 1
                decision = await provider.tool_decision(task.input_text, observation)
                if decision.get("action") == "stop":
                    _set_status(task, TaskStatus.FAILED)
                    task.error_message = step.error
                    await db.commit()
                    return
                new_plan = await provider.plan(
                    task.input_text,
                    context=context + "\nPrevious failure:\n" + (step.error or ""),
                )
                await persist_plan(db, task, new_plan)
                _set_status(task, TaskStatus.PLANNING)
                await db.commit()
                continue
            _set_status(task, TaskStatus.FAILED)
            task.error_message = step.error
            await _notify(db, task.user_id, NotificationType.TASK_FAILED, "Task failed", step.error or "Step failed", task.id)
            await db.commit()
            await hub.broadcast_user(task.user_id, {"type": "task.updated", "task_id": task.id, "status": task.status})
            return


async def _execute_step(db: AsyncSession, task: Task, step: TaskStep, project: Project | None) -> str:
    if kill_switch.is_active(task.user_id):
        step.status = StepStatus.CANCELLED.value
        return "cancelled"

    payload = dict(step.input_json or {})
    if project and not payload.get("path") and not payload.get("cwd"):
        payload.setdefault("path", project.root_path)
        payload.setdefault("cwd", project.root_path)

    target = str(payload.get("path") or payload.get("url") or payload.get("cwd") or "")
    domain = domain_from_url(payload["url"]) if payload.get("url") else None
    domain_policy = None
    if domain:
        row = (
            await db.execute(
                select(DomainPermission).where(DomainPermission.user_id == task.user_id, DomainPermission.domain == domain)
            )
        ).scalar_one_or_none()
        domain_policy = row.policy if row else "ask"

    denied = (
        await db.execute(
            select(PermissionRequest).where(
                PermissionRequest.task_id == task.id,
                PermissionRequest.tool == step.tool,
                PermissionRequest.status == PermissionRequestStatus.DENIED.value,
            )
        )
    ).scalar_one_or_none()

    platform, device_caps = await _device_caps(db, task.device_id)
    ctx = GuardianContext(
        tool=step.tool,
        action=step.tool,
        target=target,
        command=_command_preview(payload),
        domain=domain,
        contains_credentials=bool(payload.get("contains_credentials")),
        contains_payment=bool(payload.get("contains_payment")),
        contains_pii=bool(payload.get("contains_pii")),
        previously_denied=denied is not None,
        user_policy=await _policy_map(db, task.user_id),
        grants=await _grants(db, task.user_id, task.id),
        domain_policy=domain_policy,
        kill_switch_active=kill_switch.is_active(task.user_id),
        capability=capability_for_tool(step.tool),
        device_capabilities=device_caps,
        platform=platform,
        amount=payload.get("amount"),
        currency=payload.get("currency"),
        service=payload.get("service"),
        max_amount=payload.get("max_amount"),
        connector_connected=await _payment_connector_connected(db, task.user_id),
        github_connected=bool(await load_stored_token(db, task.user_id)),
        gmail_connected=bool(await load_stored_gmail_token(db, task.user_id)),
        calendar_connected=bool(await load_stored_calendar_token(db, task.user_id)),
        voice_input=bool((task.input_text or "").startswith("[voice]")),
    )
    decision = guard(ctx)
    step.risk = decision.risk.value
    step.approval_required = decision.approval_required

    await log_event(
        db,
        user_id=task.user_id,
        task_id=task.id,
        step_id=step.id,
        action="permission.decide",
        tool=step.tool,
        target=target,
        risk_level=decision.risk.value,
        permission_decision=decision.decision.value,
        extra={"reason": decision.reason},
    )

    if decision.unavailable:
        step.status = StepStatus.FAILED.value
        step.error = decision.error_code or CAPABILITY_UNAVAILABLE
        task.error_message = decision.reason
        await log_event(
            db,
            user_id=task.user_id,
            task_id=task.id,
            step_id=step.id,
            action="capability.unavailable",
            tool=step.tool,
            target=target,
            risk_level=decision.risk.value,
            permission_decision=PermissionDecision.BLOCK.value,
            extra={"reason": decision.reason, "error_code": decision.error_code or CAPABILITY_UNAVAILABLE},
        )
        await _notify(db, task.user_id, NotificationType.TOOL_UNAVAILABLE, "Capability unavailable", decision.reason, task.id)
        await db.commit()
        return "failed"

    if decision.decision == PermissionDecision.BLOCK:
        step.status = StepStatus.BLOCKED.value
        step.error = decision.reason
        task.error_message = decision.reason
        await _notify(db, task.user_id, NotificationType.SECURITY_WARNING, "Action blocked", decision.reason, task.id)
        await db.commit()
        return "blocked"

    if decision.decision == PermissionDecision.ASK:
        existing = (
            await db.execute(
                select(PermissionRequest).where(
                    PermissionRequest.step_id == step.id,
                    PermissionRequest.status == PermissionRequestStatus.PENDING.value,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = PermissionRequest(
                id=new_id(),
                user_id=task.user_id,
                task_id=task.id,
                step_id=step.id,
                action=step.description,
                tool=step.tool,
                target=target,
                command=_command_preview(payload),
                risk=decision.risk.value,
                reason=decision.reason,
                metadata_json={
                    "capability": decision.capability,
                    "platform": platform,
                    "biometric_required": decision.biometric_required,
                    "amount": payload.get("amount"),
                    "currency": payload.get("currency"),
                    "service": payload.get("service"),
                    "account": payload.get("account"),
                    "visibility": payload.get("visibility"),
                    "merchant": payload.get("merchant"),
                    "content": payload.get("content"),
                },
            )
            db.add(existing)
            await _notify(
                db,
                task.user_id,
                NotificationType.APPROVAL_REQUESTED,
                "Approval required",
                f"{step.description} ({step.tool})",
                task.id,
            )
        step.status = StepStatus.WAITING_FOR_APPROVAL.value
        _set_status(task, TaskStatus.WAITING_FOR_APPROVAL)
        await db.commit()
        await hub.broadcast_user(
            task.user_id,
            {
                "type": "approval.requested",
                "task_id": task.id,
                "request_id": existing.id,
                "action": step.description,
                "tool": step.tool,
                "command": existing.command,
                "risk": decision.risk.value,
                "reason": decision.reason,
                "capability": decision.capability,
                "biometric_required": decision.biometric_required,
                "metadata": existing.metadata_json,
            },
        )
        try:
            status = await hub.wait_approval(existing.id)
        except TimeoutError:
            step.status = StepStatus.FAILED.value
            step.error = "Approval timed out"
            return "failed"
        await db.refresh(existing)
        if status in {PermissionRequestStatus.DENIED.value, "denied"}:
            step.status = StepStatus.BLOCKED.value
            step.error = "User denied this action"
            return "blocked"
        _set_status(task, TaskStatus.RUNNING)
        await db.commit()

    if step.tool.startswith("github."):
        token = await load_stored_token(db, task.user_id)
        if not token:
            step.status = StepStatus.FAILED.value
            step.error = "CONNECTOR_NOT_CONNECTED"
            return "failed"
        if step.tool == "github.user":
            identity = await github_whoami(token)
            result = {"success": bool(identity), "data": identity or {}, "error": None if identity else "AUTHENTICATION_REQUIRED", "verification_required": True}
        else:
            result = await github_list_repos(token)
            result["verification_required"] = True
        step.output_json = redact_value(result)
        call = ToolCall(
            id=new_id(),
            task_id=task.id,
            step_id=step.id,
            tool_name=step.tool,
            input_json=redact_value(payload),
            output_json=step.output_json,
            success=bool(result.get("success")),
            verification_required=True,
            verification_status="passed" if result.get("success") else "failed",
        )
        db.add(call)
        if not result.get("success"):
            step.status = StepStatus.FAILED.value
            step.error = result.get("error_code") or result.get("error") or "ACTION_FAILED"
            await db.commit()
            return "failed"
        step.status = StepStatus.SUCCEEDED.value
        await db.commit()
        await hub.broadcast_user(task.user_id, {"type": "step.succeeded", "task_id": task.id, "step_id": step.id})
        return "ok"

    if step.tool.startswith("email.") or step.tool.startswith("gmail."):
        token = await load_stored_gmail_token(db, task.user_id)
        if not token:
            step.status = StepStatus.FAILED.value
            step.error = "CONNECTOR_NOT_CONNECTED"
            return "failed"
        if step.tool in {"email.read"} and payload.get("id"):
            result = await gmail_read(token, str(payload.get("id") or payload.get("message_id") or ""))
        elif step.tool in {"email.read", "email.search", "gmail.profile"}:
            result = await gmail_list(token, query=payload.get("query") or payload.get("q"))
        elif step.tool == "email.draft":
            result = await gmail_draft(
                token,
                to=str(payload.get("to") or ""),
                subject=str(payload.get("subject") or ""),
                body=str(payload.get("body") or payload.get("text") or ""),
            )
        elif step.tool == "email.send":
            result = await gmail_send(
                token,
                to=str(payload.get("to") or ""),
                subject=str(payload.get("subject") or ""),
                body=str(payload.get("body") or payload.get("text") or ""),
            )
        else:
            result = {"success": False, "error_code": "CAPABILITY_UNAVAILABLE", "error": step.tool}
        result["verification_required"] = True
        step.output_json = redact_value(result)
        call = ToolCall(
            id=new_id(),
            task_id=task.id,
            step_id=step.id,
            tool_name=step.tool,
            input_json=redact_value(payload),
            output_json=step.output_json,
            success=bool(result.get("success")),
            verification_required=True,
            verification_status="passed" if result.get("success") else "failed",
        )
        db.add(call)
        if not result.get("success"):
            step.status = StepStatus.FAILED.value
            step.error = result.get("error_code") or result.get("error") or "ACTION_FAILED"
            await db.commit()
            return "failed"
        step.status = StepStatus.SUCCEEDED.value
        await db.commit()
        await hub.broadcast_user(task.user_id, {"type": "step.succeeded", "task_id": task.id, "step_id": step.id})
        return "ok"

    if step.tool.startswith("calendar."):
        token = await load_stored_calendar_token(db, task.user_id)
        if not token:
            step.status = StepStatus.FAILED.value
            step.error = "CONNECTOR_NOT_CONNECTED"
            return "failed"
        if step.tool in {"calendar.write", "calendar.create"}:
            result = await calendar_create(
                token,
                summary=str(payload.get("summary") or payload.get("title") or payload.get("event") or ""),
                start=str(payload.get("start") or payload.get("start_time") or payload.get("when") or ""),
                end=str(payload.get("end") or payload.get("end_time") or "") or None,
                description=str(payload.get("description") or payload.get("body") or "") or None,
            )
        elif step.tool == "calendar.read":
            result = await calendar_list(token, query=payload.get("query") or payload.get("q"))
        else:
            result = {"success": False, "error_code": "CAPABILITY_UNAVAILABLE", "error": step.tool}
        result["verification_required"] = True
        step.output_json = redact_value(result)
        call = ToolCall(
            id=new_id(),
            task_id=task.id,
            step_id=step.id,
            tool_name=step.tool,
            input_json=redact_value(payload),
            output_json=step.output_json,
            success=bool(result.get("success")),
            verification_required=True,
            verification_status="passed" if result.get("success") else "failed",
        )
        db.add(call)
        if not result.get("success"):
            step.status = StepStatus.FAILED.value
            step.error = result.get("error_code") or result.get("error") or "ACTION_FAILED"
            await db.commit()
            return "failed"
        step.status = StepStatus.SUCCEEDED.value
        await db.commit()
        await hub.broadcast_user(task.user_id, {"type": "step.succeeded", "task_id": task.id, "step_id": step.id})
        return "ok"

    try:
        exec_tool = EXECUTE_ALIASES.get(step.tool, step.tool)
        spec = get_tool(exec_tool)
    except KeyError:
        step.status = StepStatus.FAILED.value
        step.error = f"{CAPABILITY_UNAVAILABLE}: unknown or unimplemented tool {step.tool}"
        return "failed"

    if exec_tool.startswith("terminal.") or exec_tool in {"project.run_tests", "project.run_build"}:
        executable = payload.get("executable") or payload.get("command")
        if executable:
            try:
                validate_command(str(executable), list(payload.get("args") or []))
            except TerminalDenied as exc:
                step.status = StepStatus.BLOCKED.value
                step.error = str(exc)
                return "blocked"

    if not task.device_id:
        step.status = StepStatus.FAILED.value
        step.error = "No paired device is assigned to this task"
        await _notify(db, task.user_id, NotificationType.TOOL_UNAVAILABLE, "Device unavailable", step.error, task.id)
        await db.commit()
        return "failed"

    if not hub.device_online(task.device_id):
        step.status = StepStatus.FAILED.value
        step.error = "DEVICE_OFFLINE: Device agent is not connected"
        await _notify(db, task.user_id, NotificationType.AGENT_DISCONNECTED, "Device offline", step.error, task.id)
        await db.commit()
        return "failed"

    _set_status(task, TaskStatus.RUNNING)
    step.status = StepStatus.RUNNING.value
    task.tool_calls_used += 1
    await db.commit()
    await hub.broadcast_user(task.user_id, {"type": "step.running", "task_id": task.id, "step_id": step.id, "tool": step.tool})

    folders = (await db.execute(select(AllowedFolder).where(AllowedFolder.user_id == task.user_id))).scalars().all()
    request = ToolRequest(
        task_id=task.id,
        step_id=step.id,
        tool=exec_tool,
        input=payload,
        allowed_roots=[f.path for f in folders],
        capability=decision.capability,
        timeout_seconds=int(payload.get("timeout") or 60),
    )
    try:
        response = await hub.call_tool(task.device_id, request)
    except DeviceOffline:
        step.status = StepStatus.FAILED.value
        step.error = "Device agent disconnected during execution"
        return "failed"
    except Exception as exc:
        step.status = StepStatus.FAILED.value
        step.error = str(exc)
        return "failed"

    result = redact_value(response.model_dump())
    step.output_json = result
    call = ToolCall(
        id=new_id(),
        task_id=task.id,
        step_id=step.id,
        tool_name=step.tool,
        input_json=redact_value(payload),
        output_json=result,
        success=response.success,
        verification_required=spec.verification_required,
        verification_status="pending",
    )
    db.add(call)
    await store_memory(
        db,
        user_id=task.user_id,
        kind=MemoryKind.WORKING,
        content=wrap_tool_output(step.tool, str(result)[:1500]),
        topic=step.tool,
        tool=step.tool,
        task_id=task.id,
        project_id=task.project_id,
        importance=2,
    )

    _set_status(task, TaskStatus.VERIFYING)
    step.status = StepStatus.VERIFYING.value
    await db.commit()

    verification = verify_tool(step.tool, payload, response.model_dump())
    call.verification_status = "passed" if verification["ok"] else "failed"
    await log_event(
        db,
        user_id=task.user_id,
        task_id=task.id,
        step_id=step.id,
        action=step.tool,
        tool=step.tool,
        target=target,
        risk_level=step.risk,
        permission_decision=PermissionDecision.ALLOW.value,
        result="SUCCESS" if response.success and verification["ok"] else "FAILURE",
        verification_status=call.verification_status,
    )
    if not response.success or not verification["ok"]:
        step.status = StepStatus.FAILED.value
        step.error = verification.get("reason") or response.error or "Verification failed"
        await db.commit()
        return "failed"

    step.status = StepStatus.SUCCEEDED.value
    await db.commit()
    await hub.broadcast_user(task.user_id, {"type": "step.succeeded", "task_id": task.id, "step_id": step.id})
    return "ok"


def _command_preview(payload: dict[str, Any]) -> str | None:
    if payload.get("executable"):
        args = " ".join(str(a) for a in payload.get("args") or [])
        return f"{payload['executable']} {args}".strip()
    return payload.get("command")


async def _finalize(db: AsyncSession, task: Task, provider) -> None:
    steps = sorted(task.steps, key=lambda s: s.sequence)
    if any(s.status != StepStatus.SUCCEEDED.value for s in steps):
        _set_status(task, TaskStatus.FAILED)
        task.error_message = "Not all steps succeeded; task was not marked complete"
        await db.commit()
        return
    _set_status(task, TaskStatus.VERIFYING)
    notes = []
    for step in steps:
        notes.append(f"{step.step_key}: {step.description} -> {step.status}")
    task.model_calls_used += 1
    summary = await provider.summarize("\n".join(notes) + "\nUser request: " + task.input_text)
    task.result_summary = summary
    task.verified = True
    task.status = mark_completed(task.status, verified=True).value
    task.completed_at = datetime.now(UTC)
    await summarize_working_memory(db, task.user_id, task.id)
    if task.project_id:
        await store_memory(
            db,
            user_id=task.user_id,
            kind=MemoryKind.PROJECT,
            content=summary,
            topic="last_task",
            project_id=task.project_id,
            task_id=task.id,
            importance=3,
        )
    await log_event(db, user_id=task.user_id, task_id=task.id, action="task.completed", result="SUCCESS", verification_status="passed")
    await _notify(db, task.user_id, NotificationType.TASK_COMPLETE, "Task complete", summary, task.id)
    await db.commit()
    await hub.broadcast_user(task.user_id, {"type": "task.completed", "task_id": task.id, "summary": summary})


def spawn_task(task_id: str) -> None:
    asyncio.create_task(run_task(task_id))
