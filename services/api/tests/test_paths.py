from pathlib import Path

import pytest

from app.permissions.path_guard import PathNotAllowed, validate_allowed_folder, validate_path


def test_rejects_drive_root():
    with pytest.raises(PathNotAllowed):
        validate_allowed_folder("C:\\")


def test_rejects_windows_directory():
    with pytest.raises(PathNotAllowed):
        validate_allowed_folder(r"C:\Windows\System32")


def test_rejects_appdata_as_allowed_folder():
    with pytest.raises(PathNotAllowed):
        validate_allowed_folder(r"C:\Users\User\AppData")


def test_rejects_path_traversal(tmp_path: Path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "keys.txt").write_text("nope", encoding="utf-8")
    with pytest.raises(PathNotAllowed):
        validate_path(str(allowed / ".." / "secret" / "keys.txt"), [str(allowed)])


def test_allows_path_inside_approved_folder(tmp_path: Path):
    allowed = tmp_path / "projects"
    nested = allowed / "app" / "src"
    nested.mkdir(parents=True)
    target = nested / "main.ts"
    target.write_text("ok", encoding="utf-8")
    resolved = validate_path(str(target), [str(allowed)])
    assert Path(resolved) == target.resolve()
