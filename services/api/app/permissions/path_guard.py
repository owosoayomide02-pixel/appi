"""Path sandboxing. Appi never receives full-drive access by default."""

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


def _normalize(path: str) -> Path:
    if not path or path.strip() != path and not path.strip():
        raise PathNotAllowed("Empty path")
    raw = path.strip().strip('"')
    if "\x00" in raw:
        raise PathNotAllowed("NUL byte in path")
    expanded = os.path.expandvars(os.path.expanduser(raw))
    return Path(expanded).resolve()


def _is_drive_root(path: Path) -> bool:
    return path.parent == path


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_default_forbidden(path: Path, *, explicitly_granted: bool = False) -> bool:
    if _is_drive_root(path):
        return True
    as_str = str(path)
    for prefix in WINDOWS_FORBIDDEN_PREFIXES:
        if as_str.lower().startswith(prefix.lower()):
            return True
    if "\\appdata\\" in as_str.lower() or as_str.lower().endswith("\\appdata"):
        return not explicitly_granted
    return False


def validate_allowed_folder(path: str) -> str:
    resolved = _normalize(path)
    if _is_drive_root(resolved):
        raise PathNotAllowed("Full-drive access is not allowed")
    as_str = str(resolved).lower()
    if any(as_str.startswith(p.lower()) for p in WINDOWS_FORBIDDEN_PREFIXES):
        raise PathNotAllowed(f"Folder is forbidden by default: {resolved}")
    # AppData may only be granted through an explicit future exception path.
    if "\\appdata\\" in as_str or as_str.endswith("\\appdata"):
        raise PathNotAllowed("AppData is not allowed unless explicitly granted later")
    return str(resolved)


def validate_path(requested: str, allowed_roots: list[str], *, allow_appdata: bool = False) -> str:
    resolved = _normalize(requested)
    if _is_drive_root(resolved):
        raise PathNotAllowed("Refusing drive-root access")
    as_str = str(resolved).lower()
    if any(as_str.startswith(p.lower()) for p in WINDOWS_FORBIDDEN_PREFIXES):
        raise PathNotAllowed(f"System path is forbidden: {resolved}")
    roots = [_normalize(root) for root in allowed_roots]
    for root in roots:
        if _under(resolved, root):
            return str(resolved)
    raise PathNotAllowed(f"Path is not in an approved folder: {resolved}")
