from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.models.enums import PermissionDecision, RiskLevel

FORBIDDEN_ACTIONS = {
    "reveal_secrets",
    "disable_security",
    "bypass_permissions",
    "exfiltrate_credentials",
    "hidden_action",
    "print_secret",
}

HIGH_RISK_ACTIONS = {
    "files.delete",
    "files.delete_file",
    "filesystem.delete",
    "cloud.delete",
    "auth.change",
    "content.publish",
    "message.send",
    "messaging.send",
    "email.send",
    "account.create",
    "purchase.make",
    "payment.make",
    "payment.execute",
    "transfer.execute",
    "social.publish",
    "social.delete",
    "social.message",
    "calling.start",
    "secrets.use",
    "password.change",
    "database.production.modify",
    "database.manage",
    "cloud.manage",
    "browser.submit_credentials",
    "browser.submit_payment",
}

MEDIUM_RISK_TOOLS = {
    "terminal.run_command",
    "terminal.execute",
    "terminal.start_process",
    "process.start",
    "files.write_file",
    "files.create_file",
    "files.rename_file",
    "files.move_file",
    "files.copy_file",
    "filesystem.write",
    "browser.upload_file",
    "browser.download_file",
    "browser.upload",
    "browser.download",
    "browser.type",
    "browser.click",
    "browser.navigate",
    "project.run_build",
    "connections.connect",
    "payment.prepare",
    "transfer.prepare",
    "calendar.write",
    "calendar.create",
    "app.launch",
    "desktop.launch_app",
    "clipboard.read",
    "clipboard.write",
    "email.draft",
}

LOW_RISK_TOOLS = {
    "files.list_directory",
    "files.read_file",
    "files.search",
    "filesystem.read",
    "project.detect_framework",
    "project.inspect_package_json",
    "project.inspect_git_status",
    "project.detect_errors",
    "project.run_tests",
    "browser.read_page",
    "browser.read",
    "browser.screenshot",
    "browser.open_url",
    "browser.scroll",
    "memory.retrieve",
    "social.draft",
    "access.prepare",
    "access.login",
    "calendar.read",
    "system.info",
    "project.run_tests",
    "github.user",
    "github.repos",
    "email.read",
    "email.search",
    "gmail.profile",
}

DELETE_TOOLS = {"files.delete", "files.delete_file", "files.delete_directory"}

POLICY_FIELD_BY_TOOL = {
    "files.list_directory": "read_project_files",
    "files.read_file": "read_project_files",
    "files.write_file": "edit_project_files",
    "files.create_file": "edit_project_files",
    "files.rename_file": "edit_project_files",
    "files.move_file": "edit_project_files",
    "files.copy_file": "edit_project_files",
    "files.delete_file": "delete_files",
    "files.delete": "delete_files",
    "files.search": "read_project_files",
    "project.run_tests": "run_tests",
    "terminal.run_command": "run_terminal",
    "terminal.start_process": "run_terminal",
    "terminal.stop_process": "run_terminal",
    "browser.open_browser": "use_browser",
    "browser.open_url": "use_browser",
    "browser.click": "use_browser",
    "browser.type": "use_browser",
    "browser.select": "use_browser",
    "browser.scroll": "use_browser",
    "browser.upload_file": "use_browser",
    "browser.download_file": "use_browser",
    "browser.submit": "use_browser",
    "app.launch": "use_browser",
    "desktop.launch_app": "use_browser",
    "browser.search": "use_browser",
}


@dataclass
class ActionContext:
    tool: str
    action: str
    target: str = ""
    command: str | None = None
    domain: str | None = None
    contains_credentials: bool = False
    contains_payment: bool = False
    contains_pii: bool = False
    previously_denied: bool = False
    user_policy: dict[str, str] = field(default_factory=dict)
    grants: list[dict] = field(default_factory=list)
    domain_policy: str | None = None
    kill_switch_active: bool = False


@dataclass
class DecisionResult:
    decision: PermissionDecision
    risk: RiskLevel
    reason: str
    approval_required: bool


def infer_risk(ctx: ActionContext) -> RiskLevel:
    if ctx.action in FORBIDDEN_ACTIONS or ctx.tool in FORBIDDEN_ACTIONS:
        return RiskLevel.FORBIDDEN
    if ctx.tool in DELETE_TOOLS or ctx.tool in HIGH_RISK_ACTIONS or ctx.action in HIGH_RISK_ACTIONS:
        return RiskLevel.HIGH
    if ctx.contains_credentials or ctx.contains_payment or ctx.contains_pii:
        return RiskLevel.HIGH
    if ctx.tool in MEDIUM_RISK_TOOLS:
        return RiskLevel.MEDIUM
    if ctx.tool in LOW_RISK_TOOLS:
        return RiskLevel.LOW
    return RiskLevel.MEDIUM


def _grant_covers(ctx: ActionContext, grant: dict) -> bool:
    if grant.get("revoked_at"):
        return False
    expires = grant.get("expires_at")
    if expires is not None:
        if getattr(expires, "tzinfo", None) is None:
            expires = expires.replace(tzinfo=UTC)
        if expires <= datetime.now(UTC):
            return False
    resource = grant.get("resource", "")
    tool_resource = ctx.tool.split(".")[0] if "." in ctx.tool else ctx.tool
    if resource not in {"*", tool_resource, ctx.tool, "filesystem" if tool_resource == "files" else tool_resource}:
        if resource != "browser" or tool_resource != "browser":
            if resource not in {tool_resource, ctx.action}:
                return False
    actions = grant.get("actions") or []
    verb = ctx.tool.split(".")[-1] if "." in ctx.tool else ctx.action
    if actions and "*" not in actions and verb not in actions and ctx.action not in actions:
        short = verb.replace("_file", "").replace("_directory", "")
        if short not in actions:
            return False
    scope = grant.get("scope") or "*"
    if scope != "*" and ctx.target and not ctx.target.lower().startswith(str(scope).lower()):
        if scope not in ctx.target:
            return False
    return True


def decide(ctx: ActionContext) -> DecisionResult:
    if ctx.kill_switch_active:
        return DecisionResult(PermissionDecision.BLOCK, RiskLevel.FORBIDDEN, "Kill switch is active", False)
    if ctx.previously_denied:
        return DecisionResult(
            PermissionDecision.BLOCK,
            RiskLevel.FORBIDDEN,
            "User already denied this action",
            False,
        )
    if ctx.action in FORBIDDEN_ACTIONS or ctx.tool in FORBIDDEN_ACTIONS:
        return DecisionResult(
            PermissionDecision.BLOCK,
            RiskLevel.FORBIDDEN,
            "Action is forbidden by default",
            False,
        )

    risk = infer_risk(ctx)

    matching_grants = [g for g in ctx.grants if _grant_covers(ctx, g)]
    confirmation_grant = any(g.get("requires_confirmation") for g in matching_grants)

    policy_field = POLICY_FIELD_BY_TOOL.get(ctx.tool)
    policy_value = (ctx.user_policy.get(policy_field) if policy_field else None) or ""

    if risk == RiskLevel.FORBIDDEN:
        return DecisionResult(PermissionDecision.BLOCK, risk, "Forbidden risk class", False)

    if ctx.tool.startswith("browser") and ctx.domain_policy:
        domain_policy = ctx.domain_policy.upper()
        if domain_policy in {"BLOCK"}:
            return DecisionResult(PermissionDecision.BLOCK, risk, f"Domain policy blocks {ctx.domain}", False)
        if domain_policy in {"ALWAYS_ASK", "ASK"} and not matching_grants:
            return DecisionResult(PermissionDecision.ASK, RiskLevel.HIGH if domain_policy == "ALWAYS_ASK" else risk, "Domain requires approval", True)

    if ctx.contains_credentials or ctx.contains_payment:
        return DecisionResult(PermissionDecision.ASK, RiskLevel.HIGH, "Credential or payment form requires approval", True)

    if matching_grants and not confirmation_grant and risk != RiskLevel.HIGH:
        return DecisionResult(PermissionDecision.ALLOW, risk, "Matching permission grant", False)

    if matching_grants and risk == RiskLevel.HIGH and not confirmation_grant:
        # High risk always asks unless a grant explicitly disables confirmation.
        pass

    if risk == RiskLevel.HIGH:
        return DecisionResult(PermissionDecision.ASK, risk, "High-risk actions always require approval", True)

    if policy_value == PermissionDecision.BLOCK.value:
        return DecisionResult(PermissionDecision.BLOCK, risk, "User policy blocks this action", False)
    if policy_value == PermissionDecision.ASK.value:
        return DecisionResult(PermissionDecision.ASK, risk, "User policy requires approval", True)
    if policy_value == PermissionDecision.ALLOW.value and risk == RiskLevel.LOW:
        return DecisionResult(PermissionDecision.ALLOW, risk, "User policy allows low-risk action", False)
    if policy_value == PermissionDecision.ALLOW.value and risk == RiskLevel.MEDIUM:
        return DecisionResult(PermissionDecision.ASK, risk, "Medium-risk actions require approval unless granted", True)

    if risk == RiskLevel.LOW:
        return DecisionResult(PermissionDecision.ALLOW, risk, "Low-risk default allow", False)
    if risk == RiskLevel.MEDIUM:
        return DecisionResult(PermissionDecision.ASK, risk, "Medium-risk default ask", True)
    return DecisionResult(PermissionDecision.ASK, risk, "Default ask", True)


def domain_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host
