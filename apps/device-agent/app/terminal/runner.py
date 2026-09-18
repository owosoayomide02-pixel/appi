from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform.startswith("win") else 0

import httpx

from app.security.paths import PathNotAllowed, validate_path
from app.security.terminal import TerminalDenied, validate_command

_PROCESSES: dict[str, "TrackedProcess"] = {}
_KILL = False


@dataclass
class TrackedProcess:
    id: str
    pid: int
    process: asyncio.subprocess.Process
    executable: str
    started_at: float = field(default_factory=time.time)
    log: str = ""


def set_killed(active: bool) -> None:
    global _KILL
    _KILL = active


def is_killed() -> bool:
    return _KILL


async def stop_all() -> None:
    for item in list(_PROCESSES.values()):
        await _stop(item)
    _PROCESSES.clear()


async def _stop(item: TrackedProcess) -> None:
    if item.process.returncode is None:
        item.process.terminate()
        try:
            await asyncio.wait_for(item.process.wait(), timeout=5)
        except TimeoutError:
            item.process.kill()


async def _health_check(port: int | None) -> bool | None:
    if not port:
        return None
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://127.0.0.1:{port}")
            return response.status_code < 500
    except Exception:
        return False


def _guess_port(args: list[str]) -> int | None:
    for i, arg in enumerate(args):
        if arg in {"--port", "-p"} and i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                return None
        if arg.startswith("--port="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                return None
    return 3000 if "dev" in args else None


async def execute(tool: str, payload: dict[str, Any], allowed_roots: list[str]) -> dict[str, Any]:
    if is_killed():
        return {"success": False, "error": "Kill switch is active", "verification_required": True}
    try:
        cwd = payload.get("cwd") or payload.get("path")
        if cwd:
            cwd_path = str(validate_path(cwd, allowed_roots))
        else:
            return {"success": False, "error": "Working directory must be inside an approved folder", "verification_required": True}

        if tool == "terminal.get_process_status":
            pid_key = payload.get("process_id")
            item = _PROCESSES.get(str(pid_key))
            if not item:
                return {"success": True, "data": {"running": False}, "verification_required": True}
            running = item.process.returncode is None
            return {"success": True, "data": {"running": running, "pid": item.pid, "log": item.log[-4000:]}, "verification_required": True}

        if tool == "terminal.stop_process":
            item = _PROCESSES.get(str(payload.get("process_id")))
            if not item:
                return {"success": False, "error": "Unknown process", "verification_required": True}
            await _stop(item)
            running = item.process.returncode is None
            return {"success": True, "data": {"running": running, "pid": item.pid}, "verification_required": True}

        executable = str(payload.get("executable") or payload.get("command") or "")
        args = [str(a) for a in (payload.get("args") or [])]
        if tool == "project.run_tests":
            executable, args = "npm", ["test", "--", "--watch=false"]
        if tool == "project.run_build":
            executable, args = "npm", ["run", "build"]
        validate_command(executable, args)
        timeout = int(payload.get("timeout") or payload.get("timeout_seconds") or 60)

        if tool == "terminal.start_process":
            kwargs: dict[str, Any] = {
                "cwd": cwd_path,
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.STDOUT,
                "env": {**os.environ, "CI": "1"},
            }
            if sys.platform.startswith("win"):
                kwargs["creationflags"] = _NO_WINDOW
            proc = await asyncio.create_subprocess_exec(executable, *args, **kwargs)
            tracked = TrackedProcess(id=str(uuid4()), pid=proc.pid or 0, process=proc, executable=executable)
            _PROCESSES[tracked.id] = tracked

            async def _collect() -> None:
                assert proc.stdout
                tracked.log += (await asyncio.wait_for(proc.stdout.read(8000), timeout=8)).decode("utf-8", errors="replace")

            try:
                await _collect()
            except Exception:
                pass
            port = _guess_port(args)
            health = await _health_check(port)
            return {
                "success": True,
                "data": {
                    "process_id": tracked.id,
                    "pid": tracked.pid,
                    "running": proc.returncode is None,
                    "log": tracked.log[-4000:],
                    "health": health,
                    "port": port,
                },
                "verification_required": True,
            }

        kwargs = {
            "cwd": cwd_path,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "env": {**os.environ, "CI": "1"},
        }
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = _NO_WINDOW
        proc = await asyncio.create_subprocess_exec(executable, *args, **kwargs)
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            return {"success": False, "error": "Command timed out", "verification_required": True}
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout[-20_000:],
            "stderr": stderr[-20_000:],
            "data": {"cwd": cwd_path},
            "error": None if proc.returncode == 0 else stderr[-1000:] or f"exit {proc.returncode}",
            "verification_required": True,
        }
    except (TerminalDenied, PathNotAllowed) as exc:
        return {"success": False, "error": str(exc), "verification_required": True}
    except FileNotFoundError:
        return {"success": False, "error": "Executable not found", "verification_required": True}
    except Exception as exc:
        return {"success": False, "error": str(exc), "verification_required": True}
