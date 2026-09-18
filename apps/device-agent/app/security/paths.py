"""Device-side path sandbox. Mirrors the API guard and is the enforcement layer."""

from __future__ import annotations

import os
from pathlib import Path

WINDOWS_FORBIDDEN_PREFIXES = (
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
)


class PathNotAllowed(ValueError):
    pass


def normalize(path: str) -> Path:
    raw = (path or "").strip().strip('"')
    if not raw or "\x00" in raw:
        raise PathNotAllowed("Invalid path")
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()


def validate_path(requested: str, allowed_roots: list[str]) -> Path:
    resolved = normalize(requested)
    if resolved.parent == resolved:
        raise PathNotAllowed("Refusing drive-root access")
    as_str = str(resolved).lower()
    if any(as_str.startswith(p.lower()) for p in WINDOWS_FORBIDDEN_PREFIXES):
        raise PathNotAllowed(f"System path is forbidden: {resolved}")
    if not allowed_roots:
        raise PathNotAllowed("No approved folders are configured")
    for root in allowed_roots:
        root_path = normalize(root)
        try:
            resolved.relative_to(root_path)
            return resolved
        except ValueError:
            continue
    raise PathNotAllowed(f"Path is not in an approved folder: {resolved}")
