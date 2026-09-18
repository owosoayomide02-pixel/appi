from __future__ import annotations

import json
from pathlib import Path

from app.files.ops import execute as file_execute
from app.security.paths import PathNotAllowed, validate_path


def detect_framework(root: Path) -> dict:
    if (root / "package.json").exists():
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        framework = "node"
        if "next" in deps:
            framework = "next.js"
        elif "react" in deps:
            framework = "react"
        elif "vue" in deps:
            framework = "vue"
        return {"framework": framework, "language": "TypeScript" if (root / "tsconfig.json").exists() else "JavaScript", "package": data}
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return {"framework": "python", "language": "Python"}
    if (root / "pubspec.yaml").exists():
        return {"framework": "flutter", "language": "Dart"}
    if (root / "go.mod").exists():
        return {"framework": "go", "language": "Go"}
    return {"framework": "unknown", "language": "unknown"}


def execute(tool: str, payload: dict, allowed_roots: list[str]) -> dict:
    try:
        root = validate_path(payload.get("path") or payload.get("cwd") or ".", allowed_roots)
    except PathNotAllowed as exc:
        return {"success": False, "error": str(exc), "verification_required": True}
    if tool == "project.detect_framework":
        data = detect_framework(root)
        return {"success": True, "data": data, "verification_required": True}
    if tool == "project.inspect_package_json":
        package = root / "package.json"
        if not package.exists():
            return {"success": False, "error": "package.json not found", "verification_required": True}
        data = json.loads(package.read_text(encoding="utf-8"))
        return {
            "success": True,
            "data": {
                "name": data.get("name"),
                "scripts": data.get("scripts", {}),
                "dependencies": list((data.get("dependencies") or {}).keys()),
                "devDependencies": list((data.get("devDependencies") or {}).keys()),
            },
            "verification_required": True,
        }
    if tool == "project.inspect_git_status":
        git = root / ".git"
        return {
            "success": True,
            "data": {"is_repo": git.exists(), "path": str(root)},
            "verification_required": True,
        }
    if tool == "project.detect_errors":
        listing = file_execute("files.list_directory", {"path": str(root)}, allowed_roots)
        return {"success": True, "data": {"hint": "Inspect tool logs and listing", "listing_ok": listing.get("success")}, "verification_required": True}
    return {"success": False, "error": f"Unknown project tool: {tool}", "verification_required": True}
