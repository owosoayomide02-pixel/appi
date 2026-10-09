from pathlib import Path

from app.desktop.apps import launch, search_url
from app.desktop.system import info
from app.files.ops import execute
from app.main import dispatch


def test_search_url():
    assert "FastAPI" in search_url("FastAPI documentation")


def test_launch_missing_app():
    result = launch({"app": "appi-no-such-application-xyz"})
    assert result["success"] is False
    assert result["error_code"] == "CAPABILITY_UNAVAILABLE"


def test_launch_requires_name():
    result = launch({})
    assert result["success"] is False


def test_match_start_menu_shortcut(tmp_path, monkeypatch):
    from app.desktop import apps as desktop_apps

    menu = tmp_path / "Programs"
    (menu / "Spotify.lnk").parent.mkdir(parents=True, exist_ok=True)
    (menu / "Spotify.lnk").write_bytes(b"")
    (menu / "Uninstall Spotify.lnk").write_bytes(b"")
    monkeypatch.setattr(desktop_apps, "_start_menu_roots", lambda: [menu])
    desktop_apps._CATALOG_CACHE = None
    monkeypatch.setattr(desktop_apps.sys, "platform", "win32")
    catalog = desktop_apps.installed_apps(refresh=True)
    names = [row["name"] for row in catalog]
    assert "Spotify" in names
    assert "Uninstall Spotify" not in names
    match = desktop_apps._match_shortcut("spotify")
    assert match is not None
    assert match["name"] == "Spotify"


def test_shortcut_does_not_match_unrelated_long_phrase(tmp_path, monkeypatch):
    """A short installed name must not swallow a long, unrelated request."""
    from app.desktop import apps as desktop_apps

    menu = tmp_path / "Programs"
    menu.mkdir(parents=True, exist_ok=True)
    (menu / "Appi.lnk").write_bytes(b"")
    monkeypatch.setattr(desktop_apps, "_start_menu_roots", lambda: [menu])
    desktop_apps._CATALOG_CACHE = None
    monkeypatch.setattr(desktop_apps.sys, "platform", "win32")
    desktop_apps.installed_apps(refresh=True)

    assert desktop_apps._match_shortcut("appi no such application xyz") is None
    assert desktop_apps._match_shortcut("appi") is not None


def test_system_info():
    result = info()
    assert result["success"] is True
    assert result["data"]["platform"]


def test_files_search(tmp_path: Path):
    allowed = tmp_path / "proj"
    allowed.mkdir()
    (allowed / "readme.md").write_text("hi", encoding="utf-8")
    result = execute("files.search", {"path": str(allowed), "query": "*.md"}, [str(allowed)])
    assert result["success"] is True
    assert result["data"]["count"] >= 1


def test_clipboard_roundtrip():
    from app.desktop.clipboard import read, write

    result = write("appi-clipboard-check")
    assert result["success"] is True
    got = read()
    assert got["success"] is True
    assert got["data"]["text"] == "appi-clipboard-check"


def test_windows_install_dir_is_per_user():
    from app.install_windows import install_dir, running_as_admin

    path = install_dir()
    assert "AppData" in str(path) or "Programs" in str(path)
    assert path.name == "Appi"
    assert running_as_admin() in {True, False}


def test_dispatch_system_info():
    import asyncio

    result = asyncio.run(dispatch("system.info", {}, []))
    assert result["success"] is True
    assert result["execution_mode"] == "BACKGROUND_SAFE"


def test_draft_post_never_publishes(monkeypatch):
    from app.desktop import clipboard as desktop_clipboard
    from app.desktop import handoff
    from app.desktop import apps as desktop_apps

    monkeypatch.setattr(desktop_clipboard, "write", lambda text: {"success": True, "data": {"written": True, "text": text}})
    monkeypatch.setattr(
        desktop_apps,
        "launch",
        lambda payload: {"success": True, "data": {"launched": True, "app": payload.get("app"), "url": payload.get("url")}},
    )
    result = handoff.draft_post({"platform": "instagram", "text": "Hello from Appi"})
    assert result["success"] is True
    assert result["data"]["drafted"] is True
    assert result["data"]["published"] is False
    assert "password" in result["data"]["next_step"].lower() or "paste" in result["data"]["next_step"].lower()
