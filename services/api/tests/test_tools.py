from app.tools.protocol import validate_request, validate_response
from app.tools.registry import get_tool, load_default_tools
import pytest


def test_unknown_tool_rejected():
    load_default_tools()
    with pytest.raises(KeyError):
        get_tool("os.system")


def test_invalid_tool_name_rejected():
    with pytest.raises(Exception):
        validate_request({"task_id": "t", "step_id": "s", "tool": "rm -rf", "input": {}})


def test_valid_protocol_roundtrip():
    req = validate_request(
        {
            "task_id": "task_123",
            "step_id": "step_7",
            "tool": "terminal.run_command",
            "input": {"executable": "npm", "args": ["test"]},
        }
    )
    assert req.tool == "terminal.run_command"
    ok = validate_response({"success": True, "exit_code": 0, "stdout": "ok", "stderr": "", "verification_required": True})
    assert ok.success is True
    res = validate_response(
        {
            "success": False,
            "platform": "android",
            "error": "CAPABILITY_UNAVAILABLE",
            "error_code": "CAPABILITY_UNAVAILABLE",
            "verification_required": True,
        }
    )
    assert res.error_code == "CAPABILITY_UNAVAILABLE"
    assert res.platform == "android"
