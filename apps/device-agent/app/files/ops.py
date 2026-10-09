from __future__ import annotations

from pathlib import Path

from app.security.paths import PathNotAllowed, validate_path


def _ok(data: dict, **extra) -> dict:
    payload = {"success": True, "data": data, "verification_required": True}
    payload.update(extra)
    return payload


def _err(message: str) -> dict:
    return {"success": False, "error": message, "verification_required": True}


def execute(tool: str, payload: dict, allowed_roots: list[str]) -> dict:
    try:
        if tool == "files.list_directory":
            path = validate_path(payload.get("path") or ".", allowed_roots)
            if not path.is_dir():
                return _err("Not a directory")
            entries = []
            for child in sorted(path.iterdir())[:500]:
                entries.append({"name": child.name, "is_dir": child.is_dir(), "path": str(child)})
            return _ok({"entries": entries, "path": str(path)})
        if tool == "files.read_file":
            path = validate_path(payload["path"], allowed_roots)
            if not path.is_file():
                return _err("File not found")
            if path.stat().st_size > 1_000_000:
                return _err("File too large to read")
            content = path.read_text(encoding="utf-8", errors="replace")
            return _ok({"path": str(path), "content": content, "exists": True})
        if tool in {"files.write_file", "files.create_file"}:
            path = validate_path(payload["path"], allowed_roots)
            before = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
            if tool == "files.create_file" and path.exists():
                return _err("File already exists")
            path.parent.mkdir(parents=True, exist_ok=True)
            content = payload.get("content") or ""
            path.write_text(content, encoding="utf-8")
            after = path.read_text(encoding="utf-8", errors="replace")
            return _ok({"path": str(path), "exists": path.exists(), "content": after, "before": before, "after": after})
        if tool == "files.rename_file":
            src = validate_path(payload["path"], allowed_roots)
            dest = validate_path(payload["destination"], allowed_roots)
            src.rename(dest)
            return _ok({"path": str(dest), "exists": dest.exists()})
        if tool == "files.move_file":
            src = validate_path(payload["path"], allowed_roots)
            dest = validate_path(payload["destination"], allowed_roots)
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dest)
            return _ok({"path": str(dest), "exists": dest.exists()})
        if tool == "files.copy_file":
            src = validate_path(payload["path"], allowed_roots)
            dest = validate_path(payload["destination"], allowed_roots)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            return _ok({"path": str(dest), "exists": dest.exists()})
        if tool in {"files.search", "files.find"}:
            root = validate_path(payload.get("path") or ".", allowed_roots)
            if not root.is_dir():
                return _err("Not a directory")
            query = str(payload.get("query") or payload.get("pattern") or "*").strip() or "*"
            matches = []
            for child in root.rglob(query):
                try:
                    validate_path(str(child), allowed_roots)
                except PathNotAllowed:
                    continue
                matches.append({"name": child.name, "is_dir": child.is_dir(), "path": str(child)})
                if len(matches) >= 200:
                    break
            return _ok({"path": str(root), "query": query, "matches": matches, "count": len(matches)})
        if tool == "files.delete_file":
            path = validate_path(payload["path"], allowed_roots)
            if path.is_dir():
                return _err("Refusing to delete directories in V0.1")
            if path.exists():
                path.unlink()
            return _ok({"path": str(path), "exists": path.exists()})
        return _err(f"Unknown file tool: {tool}")
    except PathNotAllowed as exc:
        return _err(str(exc))
    except KeyError as exc:
        return _err(f"Missing field: {exc}")
    except OSError as exc:
        return _err(str(exc))
