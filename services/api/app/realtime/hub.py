from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket

from app.audit.redaction import redact_value
from app.tools.protocol import ToolRequest, ToolResponse, validate_response


class DeviceOffline(RuntimeError):
    pass


class DeviceHub:
    def __init__(self) -> None:
        self.devices: dict[str, WebSocket] = {}
        self.user_sockets: dict[str, set[WebSocket]] = {}
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._approvals: dict[str, asyncio.Event] = {}
        self._approval_results: dict[str, str] = {}

    def device_online(self, device_id: str) -> bool:
        return device_id in self.devices

    async def register_device(self, device_id: str, ws: WebSocket) -> None:
        self.devices[device_id] = ws

    def unregister_device(self, device_id: str) -> None:
        self.devices.pop(device_id, None)

    async def disconnect_device(self, device_id: str) -> None:
        ws = self.devices.pop(device_id, None)
        if ws is None:
            return
        try:
            await ws.close()
        except Exception:
            pass

    async def register_ui(self, user_id: str, ws: WebSocket) -> None:
        self.user_sockets.setdefault(user_id, set()).add(ws)

    def unregister_ui(self, user_id: str, ws: WebSocket) -> None:
        sockets = self.user_sockets.get(user_id)
        if not sockets:
            return
        sockets.discard(ws)
        if not sockets:
            self.user_sockets.pop(user_id, None)

    async def broadcast_user(self, user_id: str, payload: dict[str, Any]) -> None:
        safe = redact_value(payload)
        dead: list[WebSocket] = []
        for ws in list(self.user_sockets.get(user_id, set())):
            try:
                await ws.send_json(safe)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister_ui(user_id, ws)

    async def send_device(self, device_id: str, payload: dict[str, Any]) -> None:
        ws = self.devices.get(device_id)
        if ws is None:
            raise DeviceOffline("Device agent is not connected")
        await ws.send_json(payload)

    async def call_tool(self, device_id: str, request: ToolRequest, timeout: int = 90) -> ToolResponse:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        key = f"{request.task_id}:{request.step_id}:{request.tool}"
        self._pending[key] = future
        try:
            await self.send_device(
                device_id,
                {"type": "tool.request", "payload": request.model_dump(exclude_none=True)},
            )
            raw = await asyncio.wait_for(future, timeout=timeout)
            return validate_response(raw)
        except DeviceOffline:
            raise
        except TimeoutError as exc:
            raise TimeoutError("Device agent timed out") from exc
        finally:
            self._pending.pop(key, None)

    def resolve_tool(self, task_id: str, step_id: str, tool: str, payload: dict[str, Any]) -> None:
        key = f"{task_id}:{step_id}:{tool}"
        future = self._pending.get(key)
        if future and not future.done():
            future.set_result(payload)

    def approval_event(self, request_id: str) -> asyncio.Event:
        return self._approvals.setdefault(request_id, asyncio.Event())

    def resolve_approval(self, request_id: str, status: str) -> None:
        self._approval_results[request_id] = status
        self.approval_event(request_id).set()

    async def wait_approval(self, request_id: str, timeout: int = 3600) -> str:
        await asyncio.wait_for(self.approval_event(request_id).wait(), timeout=timeout)
        return self._approval_results.get(request_id, "expired")


hub = DeviceHub()
