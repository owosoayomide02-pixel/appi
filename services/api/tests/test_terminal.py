from app.security.terminal import TerminalDenied, validate_command
import pytest


def test_blocks_format():
    with pytest.raises(TerminalDenied):
        validate_command("format", ["C:"])


def test_blocks_shutdown():
    with pytest.raises(TerminalDenied):
        validate_command("shutdown.exe", ["/s"])


def test_blocks_metacharacters_in_executable():
    with pytest.raises(TerminalDenied):
        validate_command("npm && del /f /s /q C:\\")


def test_allows_npm_test():
    validate_command("npm", ["test"])
