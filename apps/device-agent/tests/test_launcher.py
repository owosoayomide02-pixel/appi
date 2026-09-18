from pathlib import Path

from app import launcher
from app.install_windows import repo_root, write_hidden_start_script
from appi_runtime_core.autostart import windows_startup_script, windows_startup_vbs

ROOT = Path(__file__).resolve().parents[3]


def test_launcher_finds_api_and_web():
    assert (launcher.REPO_ROOT / "services" / "api" / "app").is_dir()
    assert (launcher.REPO_ROOT / "apps" / "web").is_dir()
    assert launcher.port_open(1) is False


def test_hidden_start_script_uses_launcher(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = write_hidden_start_script()
    text = path.read_text(encoding="utf-16")
    assert "app.launcher" in text
    assert "0, False" in text
    assert "WScript.Shell" in text


def test_autostart_starts_full_app_not_console_serve():
    root = repo_root()
    bat = windows_startup_script(root)
    assert "app.launcher" in bat
    vbs = windows_startup_vbs(root)
    assert "app.launcher" in vbs
    assert "0, False" in vbs


def test_start_appi_vbs_exists():
    path = ROOT / "scripts" / "Start Appi.vbs"
    text = path.read_text(encoding="utf-8")
    assert "app.launcher" in text
    assert "pythonw" in text


def test_desktop_window_is_an_application():
    from app.desktop import app_window

    assert app_window.request_show() is False
    existing = app_window.ping_existing()
    assert isinstance(existing, dict)
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert "webbrowser" not in source
    assert "run_desktop" in source
    import webview

    assert callable(webview.create_window)
