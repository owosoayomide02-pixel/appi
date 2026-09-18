from datetime import datetime
from typing import Any

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.audit.redaction import redact_text
from app.config import settings
from app.database import SessionLocal, init_db
from app.deps import rate_limit
from app.routers import (
    audit,
    auth,
    connections,
    devices,
    diffs,
    kill_switch,
    memory,
    notifications,
    onboarding,
    permissions,
    projects,
    runtime,
    tasks,
    ws,
)
from app.integrations.supabase import supabase_status
from app.providers.factory import provider_status
from app.scheduler.service import enqueue_due_jobs
from app.tools.registry import load_default_tools


def create_app() -> FastAPI:
    load_default_tools()
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await init_db()

        async def _scheduler_loop() -> None:
            while True:
                await asyncio.sleep(30)
                try:
                    async with SessionLocal() as db:
                        await enqueue_due_jobs(db)
                except Exception:
                    continue

        task = asyncio.create_task(_scheduler_loop())
        try:
            yield
        finally:
            task.cancel()

    app = FastAPI(title="APPI", version="0.1.0", description="Think. Act. Verify.", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def redact_errors(request: Request, call_next):  # type: ignore[no-untyped-def]
        try:
            await rate_limit(request)
        except Exception as exc:
            if getattr(exc, "status_code", None) == 429:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        response = await call_next(request)
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return JSONResponse({"detail": redact_text(str(exc))}, status_code=500)

    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(devices.router)
    app.include_router(kill_switch.router)
    app.include_router(permissions.router)
    app.include_router(projects.router)
    app.include_router(memory.router)
    app.include_router(connections.router)
    app.include_router(audit.router)
    app.include_router(notifications.router)
    app.include_router(onboarding.router)
    app.include_router(diffs.router)
    app.include_router(runtime.router)
    app.include_router(ws.router)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"ok": True, "service": "appi"}

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "appi-api",
            "time": datetime.utcnow().isoformat(),
            "app_url": settings.public_app_url,
            "api_url": settings.public_api_url,
            "runtime_version": settings.runtime_version,
            **provider_status(),
            **supabase_status(),
        }

    return app


app = create_app()
