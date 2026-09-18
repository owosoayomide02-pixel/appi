from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ToolHandler(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]
    risk_level: str
    required_permissions: list[str]

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    async def verify(self, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    risk_level: str
    required_permissions: list[str]
    verification_required: bool = True
    capability: str = "filesystem"
    side: str = "device"


REGISTERED_TOOLS: dict[str, ToolSpec] = {}


def register(spec: ToolSpec) -> ToolSpec:
    REGISTERED_TOOLS[spec.name] = spec
    return spec


def get_tool(name: str) -> ToolSpec:
    if name not in REGISTERED_TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return REGISTERED_TOOLS[name]


def _obj(**properties: Any) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "properties": properties}


def load_default_tools() -> None:
    if REGISTERED_TOOLS:
        return
    file_tools = [
        ("files.list_directory", "List a directory inside an approved folder", "low", ["read"], False),
        ("files.read_file", "Read a file inside an approved folder", "low", ["read"], False),
        ("files.write_file", "Write a file inside an approved folder", "medium", ["write"], True),
        ("files.create_file", "Create a file inside an approved folder", "medium", ["write"], True),
        ("files.rename_file", "Rename a file inside an approved folder", "medium", ["write"], True),
        ("files.move_file", "Move a file inside approved folders", "medium", ["write"], True),
        ("files.copy_file", "Copy a file inside approved folders", "medium", ["write"], True),
        ("files.delete_file", "Delete a file. Always elevated risk.", "high", ["delete"], True),
        ("files.search", "Search files inside an approved folder", "low", ["read"], False),
    ]
    for name, desc, risk, perms, verify in file_tools:
        register(
            ToolSpec(
                name=name,
                description=desc,
                input_schema=_obj(path={"type": "string"}, content={"type": "string"}, destination={"type": "string"}),
                risk_level=risk,
                required_permissions=perms,
                verification_required=verify,
                capability="filesystem",
            )
        )

    for name, desc, risk in [
        ("terminal.run_command", "Run a structured command (executable + args)", "medium"),
        ("terminal.start_process", "Start a background process such as a dev server", "medium"),
        ("terminal.stop_process", "Stop a tracked process", "medium"),
        ("terminal.get_process_status", "Get status of a tracked process", "low"),
    ]:
        register(
            ToolSpec(
                name=name,
                description=desc,
                input_schema=_obj(
                    executable={"type": "string"},
                    args={"type": "array", "items": {"type": "string"}},
                    cwd={"type": "string"},
                    timeout={"type": "integer"},
                    process_id={"type": "string"},
                ),
                risk_level=risk,
                required_permissions=["run"],
                capability="terminal",
            )
        )

    browser_tools = [
        ("browser.open_browser", "Launch Playwright browser", "medium"),
        ("browser.open_url", "Navigate to a URL", "medium"),
        ("browser.click", "Click an element", "medium"),
        ("browser.type", "Type into an element", "medium"),
        ("browser.read_page", "Read accessible page text", "low"),
        ("browser.screenshot", "Capture a screenshot", "low"),
        ("browser.select", "Select an option", "medium"),
        ("browser.scroll", "Scroll the page", "low"),
        ("browser.upload_file", "Upload a file", "medium"),
        ("browser.download_file", "Download a file", "medium"),
    ]
    for name, desc, risk in browser_tools:
        register(
            ToolSpec(
                name=name,
                description=desc,
                input_schema=_obj(
                    url={"type": "string"},
                    selector={"type": "string"},
                    text={"type": "string"},
                    path={"type": "string"},
                    contains_credentials={"type": "boolean"},
                    contains_payment={"type": "boolean"},
                ),
                risk_level=risk,
                required_permissions=["browse"],
                capability="browser",
            )
        )

    for name, desc, risk in [
        ("project.detect_framework", "Detect language and framework", "low"),
        ("project.inspect_package_json", "Read package.json and lockfile metadata", "low"),
        ("project.inspect_git_status", "Read git status in the project folder", "low"),
        ("project.run_tests", "Run the project test command", "low"),
        ("project.run_build", "Run the project build command", "medium"),
        ("project.detect_errors", "Collect recent error signals", "low"),
    ]:
        register(
            ToolSpec(
                name=name,
                description=desc,
                input_schema=_obj(path={"type": "string"}, command={"type": "string"}),
                risk_level=risk,
                required_permissions=["read"] if risk == "low" else ["run"],
                capability="filesystem" if "run" not in name else "terminal",
            )
        )

    register(
        ToolSpec(
            name="app.launch",
            description="Launch an installed desktop application, or open a URL in the browser",
            input_schema=_obj(app={"type": "string"}, url={"type": "string"}, query={"type": "string"}, name={"type": "string"}),
            risk_level="medium",
            required_permissions=["launch"],
            capability="desktop",
        )
    )
    register(
        ToolSpec(
            name="system.info",
            description="Read local system information",
            input_schema=_obj(),
            risk_level="low",
            required_permissions=["read"],
            verification_required=False,
            capability="system",
        )
    )
    register(
        ToolSpec(
            name="clipboard.read",
            description="Read the clipboard",
            input_schema=_obj(),
            risk_level="medium",
            required_permissions=["clipboard"],
            capability="desktop",
        )
    )
    register(
        ToolSpec(
            name="clipboard.write",
            description="Write the clipboard",
            input_schema=_obj(text={"type": "string"}, content={"type": "string"}),
            risk_level="medium",
            required_permissions=["clipboard"],
            capability="desktop",
        )
    )
    register(
        ToolSpec(
            name="github.user",
            description="Read the connected GitHub account",
            input_schema=_obj(),
            risk_level="low",
            required_permissions=["github"],
            verification_required=True,
            capability="github",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="github.repos",
            description="List repositories for the connected GitHub account",
            input_schema=_obj(),
            risk_level="low",
            required_permissions=["github"],
            verification_required=True,
            capability="github",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="gmail.profile",
            description="Read the connected Gmail account profile",
            input_schema=_obj(),
            risk_level="low",
            required_permissions=["email"],
            verification_required=True,
            capability="email",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="email.read",
            description="Read Gmail messages via the connected Google account",
            input_schema=_obj(id={"type": "string"}, message_id={"type": "string"}, query={"type": "string"}),
            risk_level="low",
            required_permissions=["email"],
            verification_required=True,
            capability="email",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="email.search",
            description="Search Gmail via the connected Google account",
            input_schema=_obj(query={"type": "string"}, q={"type": "string"}),
            risk_level="low",
            required_permissions=["email"],
            verification_required=True,
            capability="email",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="email.draft",
            description="Create a Gmail draft via the connected Google account",
            input_schema=_obj(to={"type": "string"}, subject={"type": "string"}, body={"type": "string"}, text={"type": "string"}),
            risk_level="medium",
            required_permissions=["email"],
            verification_required=True,
            capability="email",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="email.send",
            description="Send email via the connected Gmail account",
            input_schema=_obj(to={"type": "string"}, subject={"type": "string"}, body={"type": "string"}, text={"type": "string"}),
            risk_level="high",
            required_permissions=["email"],
            verification_required=True,
            capability="email",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="calendar.read",
            description="List upcoming events on the connected Google Calendar",
            input_schema=_obj(query={"type": "string"}, q={"type": "string"}),
            risk_level="low",
            required_permissions=["calendar"],
            verification_required=True,
            capability="calendar",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="calendar.write",
            description="Create an event on the connected Google Calendar",
            input_schema=_obj(
                summary={"type": "string"},
                title={"type": "string"},
                start={"type": "string"},
                end={"type": "string"},
                description={"type": "string"},
            ),
            risk_level="medium",
            required_permissions=["calendar"],
            verification_required=True,
            capability="calendar",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="calendar.create",
            description="Create an event on the connected Google Calendar",
            input_schema=_obj(
                summary={"type": "string"},
                title={"type": "string"},
                start={"type": "string"},
                end={"type": "string"},
                description={"type": "string"},
            ),
            risk_level="medium",
            required_permissions=["calendar"],
            verification_required=True,
            capability="calendar",
            side="cloud",
        )
    )
    register(
        ToolSpec(
            name="social.draft",
            description="Write a post, copy it, and open the app or site. You paste and send. Appi does not publish or type passwords.",
            input_schema=_obj(
                text={"type": "string"},
                body={"type": "string"},
                platform={"type": "string"},
                service={"type": "string"},
            ),
            risk_level="low",
            required_permissions=["draft"],
            capability="social",
        )
    )
    register(
        ToolSpec(
            name="access.prepare",
            description="Open a login page so you can sign in without typing the password from the model.",
            input_schema=_obj(service={"type": "string"}, app={"type": "string"}, platform={"type": "string"}),
            risk_level="low",
            required_permissions=["launch"],
            capability="desktop",
        )
    )
    register(
        ToolSpec(
            name="access.login",
            description="Log in with the on-device vault. Password never leaves this PC or goes to the model. MFA still needs the user.",
            input_schema=_obj(service={"type": "string"}, app={"type": "string"}, platform={"type": "string"}),
            risk_level="low",
            required_permissions=["launch"],
            capability="desktop",
        )
    )


load_default_tools()

