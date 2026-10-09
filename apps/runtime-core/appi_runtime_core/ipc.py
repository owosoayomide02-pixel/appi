"""Named localhost IPC so the dashboard is optional."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

DEFAULT_PORT = 47821


class LocalIpc:
    def __init__(self, handler: Handler, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
        self.handler = handler
        self.host = host
        self.port = port
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._client, self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await reader.readline()
            message = json.loads(raw.decode("utf-8") or "{}")
            result = await self.handler(message)
            writer.write((json.dumps(result) + "\n").encode("utf-8"))
            await writer.drain()
        except Exception as exc:
            try:
                writer.write((json.dumps({"ok": False, "error": str(exc)}) + "\n").encode("utf-8"))
                await writer.drain()
            except Exception:
                pass
        finally:
            writer.close()
            await writer.wait_closed()
