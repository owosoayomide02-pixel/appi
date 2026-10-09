"""Launch installed desktop applications without inventing success."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform.startswith("win") else 0

APP_ALIASES = {
    "chrome": ["chrome", "google-chrome", "google-chrome-stable", "chrome.exe"],
    "google chrome": ["chrome", "google-chrome", "chrome.exe"],
    "edge": ["msedge", "microsoft-edge", "msedge.exe"],
    "msedge": ["msedge", "msedge.exe"],
    "firefox": ["firefox", "firefox.exe"],
    "notepad": ["notepad", "notepad.exe"],
    "explorer": ["explorer", "explorer.exe"],
    "files": ["explorer", "explorer.exe"],
    "file explorer": ["explorer", "explorer.exe"],
    "this pc": ["explorer", "explorer.exe"],
    "code": ["code", "code.exe"],
    "vscode": ["code", "code.exe"],
    "visual studio code": ["code", "code.exe"],
    "calculator": ["calc", "calc.exe"],
    "calc": ["calc", "calc.exe"],
    "paint": ["mspaint", "mspaint.exe"],
    "word": ["winword", "winword.exe"],
    "excel": ["excel", "excel.exe"],
    "powerpoint": ["powerpnt", "powerpnt.exe"],
    "cmd": ["cmd", "cmd.exe"],
    "command prompt": ["cmd", "cmd.exe"],
    "powershell": ["powershell", "powershell.exe"],
    "settings": ["ms-settings:"],
}

_SKIP_SHORTCUT = re.compile(r"uninstall|release notes|help|readme|documentation", re.I)
_CATALOG_CACHE: list[dict[str, str]] | None = None


def _err(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": message, "error_code": code, "verification_required": True}


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data, "verification_required": True}


def search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + quote_plus(query)


def _norm(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", (name or "").lower())
    return " ".join(cleaned.split())


def _start_menu_roots() -> list[Path]:
    roots: list[Path] = []
    for env, tail in (
        ("PROGRAMDATA", r"Microsoft\Windows\Start Menu\Programs"),
        ("APPDATA", r"Microsoft\Windows\Start Menu\Programs"),
    ):
        base = os.environ.get(env)
        if base:
            roots.append(Path(base) / tail)
    return roots


def installed_apps(*, refresh: bool = False) -> list[dict[str, str]]:
    """Start Menu shortcuts on this Windows PC. Empty on other OS."""
    global _CATALOG_CACHE
    if not sys.platform.startswith("win"):
        return []
    if _CATALOG_CACHE is not None and not refresh:
        return _CATALOG_CACHE
    found: dict[str, dict[str, str]] = {}
    for root in _start_menu_roots():
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".lnk", ".appref-ms", ".url"}:
                continue
            label = path.stem.strip()
            if not label or _SKIP_SHORTCUT.search(label):
                continue
            key = _norm(label)
            if not key or key in found:
                continue
            found[key] = {"name": label, "path": str(path), "key": key}
    _CATALOG_CACHE = sorted(found.values(), key=lambda row: row["name"].lower())
    return _CATALOG_CACHE


def _app_paths_exe(name: str) -> str | None:
    if not sys.platform.startswith("win"):
        return None
    try:
        import winreg
    except ImportError:
        return None
    key_name = name if name.lower().endswith(".exe") else f"{name}.exe"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{key_name}") as handle:
                value, _ = winreg.QueryValueEx(handle, "")
        except OSError:
            continue
        if value and os.path.isfile(value):
            return value
    return None


def _windows_exe(name: str) -> str | None:
    key = name.lower().replace(".exe", "").strip()
    candidates = APP_ALIASES.get(key, [name, f"{key}.exe"])
    extra = []
    if key in {"chrome", "google chrome"}:
        extra = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    if key in {"edge", "msedge"}:
        extra = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
    for path in extra:
        if path and os.path.isfile(path):
            return path
    for candidate in candidates:
        if candidate.endswith(":") and candidate.startswith("ms-"):
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return _app_paths_exe(key)


def _words(value: str) -> list[str]:
    return [word for word in value.split() if word]


def _has_all_words(key: str, tokens: list[str]) -> bool:
    key_words = set(_words(key))
    return bool(tokens) and all(token in key_words for token in tokens)


def _match_shortcut(name: str) -> dict[str, str] | None:
    spoken = _norm(name)
    if not spoken:
        return None
    catalog = installed_apps()
    exact = [row for row in catalog if row["key"] == spoken]
    if exact:
        return exact[0]

    # "spot" may open "Spotify": the spoken phrase must open the app name.
    candidates = [row for row in catalog if len(spoken) >= 2 and row["key"].startswith(spoken)]

    # "spotify music" may open "Spotify", but "appi no such application xyz"
    # must not open "Appi". Require the app name to cover most of the phrase.
    for row in catalog:
        key = row["key"]
        if spoken.startswith(f"{key} ") and len(key) >= len(spoken) / 2:
            candidates.append(row)

    if not candidates:
        candidates = [row for row in catalog if _has_all_words(row["key"], _words(spoken))]
    if not candidates:
        return None
    candidates.sort(key=lambda row: (abs(len(row["key"]) - len(spoken)), len(row["key"])))
    return candidates[0]


def voice_open_phrases(limit: int = 100) -> list[str]:
    phrases = [
        "open chrome",
        "open notepad",
        "open files",
        "open calculator",
        "open paint",
        "open settings",
        "open edge",
        "open vscode",
        "open command prompt",
    ]
    for row in installed_apps()[:limit]:
        phrases.append(f"open {row['name']}")
        phrases.append(f"launch {row['name']}")
    seen: set[str] = set()
    unique: list[str] = []
    for phrase in phrases:
        key = _norm(phrase)
        if key in seen:
            continue
        seen.add(key)
        unique.append(phrase)
    return unique[: limit * 2]


def write_voice_commands(base: Path | None = None) -> Path:
    """Merge core phrases with Start Menu app names for Windows Speech Recognition."""
    root = Path(os.environ.get("APPDATA") or Path.home()) / "Appi"
    root.mkdir(parents=True, exist_ok=True)
    dest = root / "voice-commands.txt"
    lines: list[str] = []
    source = base
    if source is None:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            source = Path(sys._MEIPASS) / "scripts" / "commands.txt"
        else:
            source = Path(__file__).resolve().parents[4] / "services" / "voice" / "scripts" / "commands.txt"
    if source.is_file():
        lines.extend(source.read_text(encoding="utf-8").splitlines())
    lines.append("# Installed Start Menu apps on this PC")
    lines.extend(voice_open_phrases())
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def launch(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("app") or payload.get("name") or payload.get("target") or "").strip()
    url = payload.get("url")
    query = payload.get("query") or payload.get("search")
    if query and not url:
        url = search_url(str(query))
    if not name and url:
        name = "chrome" if sys.platform.startswith("win") else "browser"
    if not name:
        return _err("ACTION_FAILED", "No application name provided")

    if sys.platform.startswith("win"):
        alias = APP_ALIASES.get(_norm(name), [])
        if alias and alias[0].startswith("ms-"):
            try:
                os.startfile(alias[0])  # type: ignore[attr-defined]
                return _ok({"app": name, "launched": True, "method": "protocol"})
            except OSError as exc:
                return _err("CAPABILITY_UNAVAILABLE", str(exc))
        exe = _windows_exe(name)
        shortcut = None if exe else _match_shortcut(name)
        if shortcut:
            try:
                os.startfile(shortcut["path"])  # type: ignore[attr-defined]
                return _ok({"app": shortcut["name"], "path": shortcut["path"], "launched": True, "method": "start-menu"})
            except OSError as exc:
                return _err("CAPABILITY_UNAVAILABLE", str(exc))
        if not exe and url:
            try:
                os.startfile(str(url))  # type: ignore[attr-defined]
                return _ok({"app": name, "url": url, "launched": True, "method": "os.startfile"})
            except OSError as exc:
                return _err("CAPABILITY_UNAVAILABLE", str(exc))
        if not exe:
            return _err("CAPABILITY_UNAVAILABLE", f"Application not found: {name}")
        args = [exe] + ([str(url)] if url else [])
        proc = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        return _ok({"app": exe, "url": url, "pid": proc.pid, "launched": True, "method": "exec"})

    if sys.platform == "darwin":
        args = ["open", "-a", name] + ([str(url)] if url else [])
        completed = subprocess.run(args, capture_output=True, text=True)
        if completed.returncode == 0:
            return _ok({"app": name, "url": url, "launched": True, "method": "open -a"})

    key = name.lower().replace(".exe", "")
    candidates = APP_ALIASES.get(key, [name])
    binary = next((c for c in candidates if shutil.which(c)), None)
    if binary:
        args = [binary] + ([str(url)] if url else [])
        proc = subprocess.Popen(args)
        return _ok({"app": binary, "url": url, "pid": proc.pid, "launched": True, "method": "exec"})
    if url:
        import webbrowser

        opened = webbrowser.open(str(url))
        if opened:
            return _ok({"app": name, "url": url, "launched": True, "method": "webbrowser"})
    return _err("CAPABILITY_UNAVAILABLE", f"Application not found: {name}")
