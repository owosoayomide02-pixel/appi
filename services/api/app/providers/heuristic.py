from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from app.permissions.engine import infer_risk
from app.permissions.engine import ActionContext
from app.providers.base import ModelProvider, PlanModel, PlanStepModel


def _step(index: int, description: str, tool: str, **input_data: Any) -> PlanStepModel:
    ctx = ActionContext(tool=tool, action=tool, target=str(input_data.get("path") or input_data.get("url") or input_data.get("app") or ""))
    risk = infer_risk(ctx)
    return PlanStepModel(
        id=f"step_{index}",
        description=description,
        tool=tool,
        risk=risk.value,
        depends_on=[] if index == 1 else [f"step_{index - 1}"],
        approval_required=risk.value in {"medium", "high"},
        input=input_data,
    )


def _finalize(goal: str, steps: list[PlanStepModel]) -> PlanModel:
    steps = steps[:10]
    for i, step in enumerate(steps, start=1):
        step.id = f"step_{i}"
        step.depends_on = [] if i == 1 else [f"step_{i - 1}"]
    return PlanModel(goal=goal.strip()[:300] or "Complete the requested task", steps=steps)


def _search_query(goal: str) -> str:
    match = re.search(r"search(?:\s+the\s+web)?(?:\s+for)?\s+(.+)$", goal, re.I)
    if match:
        return match.group(1).strip().rstrip(".!?")
    return goal.strip()


def _post_body(goal: str) -> str:
    raw = re.sub(r"^\[voice\]\s*", "", goal.strip(), flags=re.I)
    match = re.search(r"(?:saying|that says|that reads|caption(?:ed)?|about|:\s+)(.+)$", raw, re.I | re.S)
    if match:
        return match.group(1).strip().strip('"').strip()
    cleaned = re.sub(
        r"^(?:appi[,:\s]*)?(?:please\s+)?(?:write|draft|create|make|post|publish|share|tweet)\s+"
        r"(?:an?\s+)?(?:instagram\s+|facebook\s+|tiktok\s+|linkedin\s+|twitter\s+|x\s+|whatsapp\s+)?"
        r"(?:post|tweet|caption|update|status)?\s*(?:for me\s*)?",
        "",
        raw,
        flags=re.I,
    ).strip()
    return cleaned or raw


def _amount(text: str) -> float | None:
    match = re.search(r"(?:₦|ngn\s*)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text, re.I)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def heuristic_plan(goal: str, *, project_path: str | None = None) -> PlanModel:
    raw = goal
    if raw.lower().startswith("[voice]"):
        raw = raw.split("]", 1)[-1].strip()
    text = raw.lower()
    steps: list[PlanStepModel] = []
    cwd = project_path or ""

    def add(description: str, tool: str, **kwargs: Any) -> None:
        steps.append(_step(len(steps) + 1, description, tool, **kwargs))

    if "transfer" in text or "send money" in text or "₦" in raw:
        amount = _amount(raw) or 0
        add(
            "Execute a financial transfer if a connector is connected",
            "transfer.execute",
            amount=amount,
            currency="NGN",
        )
        return _finalize(goal, steps)

    loginish = any(
        token in text
        for token in ("log in", "login", "sign in", "signin", "connect my", "connect to", "create an account", "sign up", "signup")
    )
    if loginish and not any(token in text for token in ("instagram post", "facebook post", "write a post")):
        service = ""
        for name in ("gmail", "google", "github", "instagram", "facebook", "linkedin", "whatsapp", "twitter"):
            if name in text:
                service = "x" if name == "twitter" else name
                break
        if service:
            add(
                f"Log into {service} using the local vault. Password stays on the device.",
                "access.login",
                service=service,
            )
            return _finalize(goal, steps)

    socialish = any(
        token in text
        for token in (
            "instagram",
            "facebook",
            "tiktok",
            "linkedin",
            "whatsapp",
            "threads",
            "twitter",
            "tweet",
            "write a post",
            "draft a post",
            "write a caption",
            "post about",
            "post this",
        )
    ) or bool(re.search(r"\bon x\b", text))
    if socialish and "send money" not in text:
        platform = ""
        for name, key in (
            ("instagram", "instagram"),
            ("facebook", "facebook"),
            ("tiktok", "tiktok"),
            ("linkedin", "linkedin"),
            ("whatsapp", "whatsapp"),
            ("threads", "threads"),
            ("twitter", "x"),
            ("tweet", "x"),
        ):
            if name in text:
                platform = key
                break
        if not platform and re.search(r"\bon x\b", text):
            platform = "x"
        body = _post_body(raw)
        add(
            "Draft the post, copy it, and open the app. You paste and send.",
            "social.draft",
            platform=platform,
            text=body,
        )
        return _finalize(goal, steps)

    if "github" in text:
        if "repo" in text:
            add("List repositories on the connected GitHub account", "github.repos")
        else:
            add("Read the connected GitHub account", "github.user")
        return _finalize(goal, steps)

    emailish = "gmail" in text or "inbox" in text or "email" in text
    if emailish and "send money" not in text:
        to_match = re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", raw, re.I)
        to_addr = to_match.group(0) if to_match else ""
        if "draft" in text:
            add("Create a Gmail draft", "email.draft", to=to_addr, subject="", body=raw)
        elif "send" in text:
            add("Send email via connected Gmail", "email.send", to=to_addr, subject="", body=raw)
        elif "search" in text:
            add("Search Gmail", "email.search", query=_search_query(raw))
        else:
            add("Read Gmail via the connected account", "email.read")
        return _finalize(goal, steps)

    if "calendar" in text or "meeting" in text or "schedule" in text:
        write = any(token in text for token in ("create", "add", "book")) or "schedule a" in text or "schedule an" in text
        if write:
            add("Create a Google Calendar event", "calendar.write", summary=raw, start="", end="")
        else:
            add("Read upcoming Google Calendar events", "calendar.read")
        return _finalize(goal, steps)

    if "delete" in text and "project" in text:
        add("Delete the requested project file after Guardian approval", "files.delete_file", path=cwd or ".")
        return _finalize(goal, steps)

    chrome_search = "chrome" in text or (
        "search" in text and any(token in text for token in ("open", "google", "browser", "web"))
    )
    if chrome_search and "test" not in text:
        if "search" in text:
            query = _search_query(raw)
            url = "https://www.google.com/search?q=" + quote_plus(query)
            add("Launch Chrome and open the search", "app.launch", app="chrome", url=url, query=query)
        else:
            add("Launch Chrome", "app.launch", app="chrome")
        return _finalize(goal, steps)

    open_app = re.match(
        r"^(?:appi[,:\s]*)?(?:please\s+)?(?:open|launch|start)\s+(?:up\s+)?(?:the\s+)?(.+?)(?:\s+for me)?$",
        text.strip(),
        re.I,
    )
    if open_app:
        app_name = open_app.group(1).strip().rstrip(".!?")
        app_name = re.sub(r"^(the\s+|app\s+)", "", app_name).strip()
        blocked = {
            "file",
            "a file",
            "my project",
            "project",
            "browser",
            "the browser",
            "website",
            "url",
            "http",
        }
        if app_name and app_name not in blocked and "project" not in app_name and "http" not in app_name:
            add(f"Open {app_name}", "app.launch", app=app_name)
            return _finalize(goal, steps)

    if re.search(r"run .{0,40}test", text) or ( "test" in text and "open" in text and "project" in text):
        add("Run the project tests in the background", "project.run_tests", path=cwd or ".")
        return _finalize(goal, steps)

    coding = any(
        token in text
        for token in ("fix", "error", "bug", "npm", "test", "build", "server", "code", "project", "auth", "lint")
    )
    browser = any(token in text for token in ("browser", "open http", "website", "url", "login page", "form"))
    wants_tests = "test" in text
    wants_dev = any(token in text for token in ("npm run dev", "dev server", "start", "restart"))
    wants_fix = any(token in text for token in ("fix", "repair", "resolve"))

    wants_write = any(token in text for token in ("write a file", "create a file", "save this file"))
    if wants_write and not coding and not browser:
        add("Write to an approved file", "files.write_file", path=cwd or ".", content="appi-runtime-check\n")
        add("Verify the file exists", "files.read_file", path=cwd or ".")
        return _finalize(goal, steps)

    if coding:
        add("Inspect project files and layout", "files.list_directory", path=cwd or ".")
        add("Detect language and framework", "project.detect_framework", path=cwd or ".")
        add("Inspect package.json / project manifests", "project.inspect_package_json", path=cwd or ".")
        add("Inspect git status", "project.inspect_git_status", path=cwd or ".")
        if wants_dev or "fail" in text:
            add("Run the development server to capture the error", "terminal.start_process", executable="npm", args=["run", "dev"], cwd=cwd)
            add("Read the captured error output", "project.detect_errors", path=cwd or ".")
        add("Locate related source files", "files.read_file", path=cwd or ".")
        if wants_fix:
            add("Apply a reversible code fix in approved files", "files.write_file", path=cwd or ".")
        if wants_dev:
            add("Restart the development server", "terminal.start_process", executable="npm", args=["run", "dev"], cwd=cwd)
        if wants_tests or wants_fix:
            add("Run tests", "project.run_tests", path=cwd or ".")
        add("Verify the result", "project.detect_errors", path=cwd or ".")
    elif browser:
        add("Open the browser", "browser.open_browser")
        url = _extract_url(raw) or "https://example.com"
        add("Navigate to the requested page", "browser.open_url", url=url)
        add("Read the page content", "browser.read_page")
        if any(token in text for token in ("fill", "form", "type", "login")):
            add("Fill the form (approval required before submitting credentials)", "browser.type")
        add("Capture a screenshot for verification", "browser.screenshot")
    else:
        add("Inspect approved workspace files", "files.list_directory", path=cwd or ".")
        add("Read relevant files", "files.read_file", path=cwd or ".")
        if "run" in text or "command" in text:
            add("Run the requested command if permitted", "terminal.run_command", executable="cmd", args=["/c", "echo", "pending"], cwd=cwd)
        add("Summarize findings", "project.detect_errors", path=cwd or ".")

    return _finalize(goal, steps)


def _extract_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0) if match else None


class HeuristicProvider(ModelProvider):
    name = "heuristic"

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        return "Heuristic provider is active. Configure AI_PROVIDER and AI_API_KEY for model-generated text."

    async def plan(self, goal: str, *, context: str = "") -> PlanModel:
        path = None
        if "Project path:" in context:
            path = context.split("Project path:", 1)[1].splitlines()[0].strip()
        return heuristic_plan(goal, project_path=path or None)

    async def classify_action(self, description: str) -> dict[str, Any]:
        lowered = description.lower()
        if any(word in lowered for word in ("delete", "payment", "password", "secret", "transfer")):
            category = "high"
        elif any(word in lowered for word in ("write", "install", "run", "start", "launch")):
            category = "medium"
        else:
            category = "low"
        return {"risk": category, "description": description}

    async def summarize(self, text: str) -> str:
        compact = " ".join(text.split())
        return compact[:600]

    async def tool_decision(self, goal: str, observation: str) -> dict[str, Any]:
        failed = "error" in observation.lower() or "failed" in observation.lower()
        return {"action": "replan" if failed else "continue", "reason": observation[:400]}
