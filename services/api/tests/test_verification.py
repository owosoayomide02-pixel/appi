from app.verification.engine import verify_tool


def test_write_requires_file_to_exist():
    result = verify_tool(
        "files.write_file",
        {"content": "hello"},
        {"success": True, "data": {"exists": False}},
    )
    assert result["ok"] is False


def test_write_success_when_content_matches():
    result = verify_tool(
        "files.write_file",
        {"content": "hello"},
        {"success": True, "data": {"exists": True, "content": "hello"}},
    )
    assert result["ok"] is True


def test_command_nonzero_exit_fails_verification():
    result = verify_tool("terminal.run_command", {}, {"success": True, "exit_code": 1, "data": {}})
    assert result["ok"] is False


def test_browser_mfa_pauses():
    result = verify_tool(
        "browser.open_url",
        {"url": "https://example.com"},
        {"success": True, "data": {"url": "https://example.com", "mfa_required": True}},
    )
    assert result["ok"] is False
    assert "MFA" in result["reason"]
