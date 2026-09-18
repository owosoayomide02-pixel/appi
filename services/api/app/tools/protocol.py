from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, field_validator

TOOL_NAME_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"

TOOL_REQUEST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "step_id", "tool", "input"],
    "properties": {
        "task_id": {"type": "string", "minLength": 1},
        "step_id": {"type": "string", "minLength": 1},
        "tool": {"type": "string", "pattern": TOOL_NAME_PATTERN},
        "input": {"type": "object"},
        "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 600},
        "timeout": {"type": "integer", "minimum": 1, "maximum": 600},
        "permission_token": {"type": "string"},
        "allowed_roots": {"type": "array", "items": {"type": "string"}},
        "capability": {"type": "string"},
    },
}

TOOL_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "exit_code": {"type": ["integer", "null"]},
        "stdout": {"type": "string"},
        "stderr": {"type": "string"},
        "data": {},
        "error": {"type": ["string", "null"]},
        "verification_required": {"type": "boolean"},
        "verification": {"type": ["object", "null"]},
        "platform": {"type": "string"},
        "result": {},
        "error_code": {"type": ["string", "null"]},
    },
}

_request_validator = Draft202012Validator(TOOL_REQUEST_SCHEMA)
_response_validator = Draft202012Validator(TOOL_RESPONSE_SCHEMA)


class ToolRequest(BaseModel):
    task_id: str
    step_id: str
    tool: str
    input: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60
    timeout: int | None = None
    permission_token: str | None = None
    allowed_roots: list[str] = Field(default_factory=list)
    capability: str | None = None

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, value: str) -> str:
        import re

        if not re.match(TOOL_NAME_PATTERN, value):
            raise ValueError("Invalid tool name")
        return value


class ToolResponse(BaseModel):
    success: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    data: Any = None
    error: str | None = None
    verification_required: bool = True
    verification: dict[str, Any] | None = None
    platform: str | None = None
    result: Any = None
    error_code: str | None = None


def validate_request(payload: dict[str, Any]) -> ToolRequest:
    errors = sorted(_request_validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        raise ValueError(errors[0].message)
    return ToolRequest.model_validate(payload)


def validate_response(payload: dict[str, Any]) -> ToolResponse:
    allowed = {
        "success",
        "exit_code",
        "stdout",
        "stderr",
        "data",
        "error",
        "verification_required",
        "verification",
        "platform",
        "result",
        "error_code",
    }
    cleaned = {key: value for key, value in payload.items() if key in allowed}
    errors = sorted(_response_validator.iter_errors(cleaned), key=lambda e: e.path)
    if errors:
        raise ValueError(errors[0].message)
    return ToolResponse.model_validate(cleaned)
