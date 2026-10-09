from pathlib import Path

import pytest

from app.files.ops import execute
from app.security.paths import PathNotAllowed, validate_path
from app.security.terminal import TerminalDenied, validate_command
from app.runtime_profile import desktop_capabilities


def test_windows_profile_is_honest():
    caps = desktop_capabilities("windows")
    assert caps["filesystem"] is True
    assert caps["terminal"] is True
    assert caps["browser"] is True
    assert caps["desktop.launch_app"] is True
    assert caps["clipboard.read"] is True
    assert caps["system.info"] is True
    assert caps["social.draft"] is True
    assert caps["social.publish"] is False
    assert caps["payment.execute"] is False
    assert caps["contacts.read"] is False


def test_file_read_outside_root_fails(tmp_path: Path):
    allowed = tmp_path / "ok"
    allowed.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    secret = other / "secret.txt"
    secret.write_text("classified", encoding="utf-8")
    result = execute("files.read_file", {"path": str(secret)}, [str(allowed)])
    assert result["success"] is False


def test_write_and_verify_inside_root(tmp_path: Path):
    allowed = tmp_path / "proj"
    allowed.mkdir()
    target = allowed / "app.ts"
    result = execute("files.write_file", {"path": str(target), "content": "export {}\n"}, [str(allowed)])
    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "export {}\n"
    assert result["data"]["exists"] is True


def test_delete_directory_refused(tmp_path: Path):
    allowed = tmp_path / "proj"
    allowed.mkdir()
    result = execute("files.delete_file", {"path": str(allowed)}, [str(allowed)])
    assert result["success"] is False


def test_terminal_blocks_reg():
    with pytest.raises(TerminalDenied):
        validate_command("reg.exe", ["delete", "HKLM\\something"])


def test_path_rejects_windows():
    with pytest.raises(PathNotAllowed):
        validate_path(r"C:\Windows\System32\cmd.exe", [r"C:\Users\User\Projects"])
