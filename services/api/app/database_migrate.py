from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError

from app.database import Base


def ensure_sqlite_columns(sync_conn: Connection) -> None:
    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())
    additions: dict[str, list[tuple[str, str]]] = {
        "devices": [
            ("platform", "VARCHAR(32) DEFAULT 'windows'"),
            ("runtime_version", "VARCHAR(32) DEFAULT '0.2.0'"),
            ("capabilities_json", "TEXT DEFAULT '{}'"),
            ("voice_json", "TEXT DEFAULT '{}'"),
            ("last_heartbeat_at", "DATETIME"),
            ("revoked_at", "DATETIME"),
        ],
        "permission_requests": [
            ("metadata_json", "TEXT DEFAULT '{}'"),
        ],
        "connections": [
            ("category", "VARCHAR(40) DEFAULT 'developer'"),
        ],
    }
    for table, cols in additions.items():
        if table not in tables:
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name, ddl in cols:
            if name not in existing:
                try:
                    sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                except OperationalError as exc:
                    if "duplicate column" not in str(exc).lower():
                        raise
