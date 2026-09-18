"""Appi Guardian — capability check then ALLOW / ASK / BLOCK.

The model cannot bypass this flow.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import PermissionDecision, RiskLevel
from app.permissions.engine import ActionContext, DecisionResult, decide
from app.runtime.capabilities import (
    CAPABILITY_UNAVAILABLE,
    capability_for_tool,
    capability_implemented,
    device_has_capability,
)

CONNECTOR_NOT_CONNECTED = "CONNECTOR_NOT_CONNECTED"
AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"

PAYMENT_TOOLS = {
    "payment.execute",
    "payment.prepare",
    "transfer.execute",
    "transfer.prepare",
    "bill.pay",
}

GITHUB_TOOLS = {
    "github.user",
    "github.repos",
}

GMAIL_READ_TOOLS = {
    "email.read",
    "email.search",
    "gmail.profile",
}
GMAIL_WRITE_TOOLS = {
    "email.draft",
    "email.send",
}

CALENDAR_READ_TOOLS = {
    "calendar.read",
}
CALENDAR_WRITE_TOOLS = {
    "calendar.write",
    "calendar.create",
}

# Capability-specific defaults (permissions are still separate from support).
CAPABILITY_POLICY = {
    "social.draft": PermissionDecision.ALLOW,
    "access.prepare": PermissionDecision.ALLOW,
    "access.login": PermissionDecision.ALLOW,
    "social.publish": PermissionDecision.ASK,
    "social.delete": PermissionDecision.ASK,
    "social.message": PermissionDecision.ASK,
    "payment.prepare": PermissionDecision.ASK,
    "payment.execute": PermissionDecision.ASK,
    "messaging.send": PermissionDecision.ASK,
    "calling.start": PermissionDecision.ASK,
    "email.send": PermissionDecision.ASK,
    "email.draft": PermissionDecision.ASK,
    "calendar.write": PermissionDecision.ASK,
}


@dataclass
class GuardianContext(ActionContext):
    capability: str = ""
    device_capabilities: dict | None = None
    platform: str = "windows"
    amount: float | None = None
    currency: str | None = None
    service: str | None = None
    max_amount: float | None = None
    biometric_required: bool = False
    connector_connected: bool | None = None
    github_connected: bool = False
    gmail_connected: bool = False
    calendar_connected: bool = False
    voice_input: bool = False


@dataclass
class GuardianResult(DecisionResult):
    capability: str = ""
    unavailable: bool = False
    error_code: str | None = None
    biometric_required: bool = False


def guard(ctx: GuardianContext) -> GuardianResult:
    capability = ctx.capability or capability_for_tool(ctx.tool)

    if ctx.kill_switch_active:
        return GuardianResult(
            PermissionDecision.BLOCK,
            RiskLevel.FORBIDDEN,
            "Kill switch is active",
            False,
            capability=capability,
            error_code="KILL_SWITCH",
        )

    if ctx.tool in PAYMENT_TOOLS or capability in {"payment.execute", "payment.prepare"}:
        if ctx.connector_connected is False or ctx.connector_connected is None:
            return GuardianResult(
                PermissionDecision.BLOCK,
                RiskLevel.HIGH,
                f"{CONNECTOR_NOT_CONNECTED}: no approved financial connector is connected",
                False,
                capability=capability,
                unavailable=True,
                error_code=CONNECTOR_NOT_CONNECTED,
                biometric_required=True,
            )
        if ctx.voice_input:
            return GuardianResult(
                PermissionDecision.ASK,
                RiskLevel.HIGH,
                f"{AUTHENTICATION_REQUIRED}: voice is not sufficient for financial actions",
                True,
                capability=capability,
                error_code=AUTHENTICATION_REQUIRED,
                biometric_required=True,
            )

    if ctx.tool in GITHUB_TOOLS or capability == "github.read":
        if not ctx.github_connected:
            return GuardianResult(
                PermissionDecision.BLOCK,
                RiskLevel.MEDIUM,
                f"{CONNECTOR_NOT_CONNECTED}: GitHub is not connected",
                False,
                capability="github.read",
                unavailable=True,
                error_code=CONNECTOR_NOT_CONNECTED,
            )
        return GuardianResult(
            PermissionDecision.ALLOW,
            RiskLevel.LOW,
            "GitHub read via connected account",
            False,
            capability="github.read",
        )

    if ctx.tool in GMAIL_READ_TOOLS | GMAIL_WRITE_TOOLS or capability in {"email.read", "email.send"}:
        if not ctx.gmail_connected:
            return GuardianResult(
                PermissionDecision.BLOCK,
                RiskLevel.MEDIUM,
                f"{CONNECTOR_NOT_CONNECTED}: Gmail is not connected",
                False,
                capability="email.send" if ctx.tool in GMAIL_WRITE_TOOLS else "email.read",
                unavailable=True,
                error_code=CONNECTOR_NOT_CONNECTED,
            )
        if ctx.tool == "email.send":
            return GuardianResult(
                PermissionDecision.ASK,
                RiskLevel.HIGH,
                "Sending email always requires approval",
                True,
                capability="email.send",
            )
        if ctx.tool == "email.draft":
            return GuardianResult(
                PermissionDecision.ASK,
                RiskLevel.MEDIUM,
                "Creating a Gmail draft requires approval",
                True,
                capability="email.read",
            )
        return GuardianResult(
            PermissionDecision.ALLOW,
            RiskLevel.LOW,
            "Gmail read via connected account",
            False,
            capability="email.read",
        )

    if ctx.tool in CALENDAR_READ_TOOLS | CALENDAR_WRITE_TOOLS or capability in {"calendar.read", "calendar.write"}:
        if not ctx.calendar_connected:
            return GuardianResult(
                PermissionDecision.BLOCK,
                RiskLevel.MEDIUM,
                f"{CONNECTOR_NOT_CONNECTED}: Google Calendar is not connected",
                False,
                capability="calendar.write" if ctx.tool in CALENDAR_WRITE_TOOLS else "calendar.read",
                unavailable=True,
                error_code=CONNECTOR_NOT_CONNECTED,
            )
        if ctx.tool in CALENDAR_WRITE_TOOLS:
            return GuardianResult(
                PermissionDecision.ASK,
                RiskLevel.MEDIUM,
                "Creating a calendar event requires approval",
                True,
                capability="calendar.write",
            )
        return GuardianResult(
            PermissionDecision.ALLOW,
            RiskLevel.LOW,
            "Calendar read via connected account",
            False,
            capability="calendar.read",
        )

    implemented = capability_implemented(capability, ctx.platform)
    present = True
    if ctx.device_capabilities is not None:
        present = device_has_capability(ctx.device_capabilities, capability)
    if not implemented or not present:
        return GuardianResult(
            PermissionDecision.BLOCK,
            RiskLevel.FORBIDDEN,
            f"{CAPABILITY_UNAVAILABLE}: {capability} is not available on {ctx.platform}",
            False,
            capability=capability,
            unavailable=True,
            error_code=CAPABILITY_UNAVAILABLE,
        )

    if capability == "payment.execute":
        ctx.biometric_required = True
        if ctx.max_amount is not None and ctx.amount is not None and ctx.amount > ctx.max_amount:
            return GuardianResult(
                PermissionDecision.ASK,
                RiskLevel.HIGH,
                f"Amount exceeds limit ({ctx.amount} > {ctx.max_amount} {ctx.currency or ''})".strip(),
                True,
                capability=capability,
                biometric_required=True,
            )

    base = decide(ctx)
    policy = CAPABILITY_POLICY.get(ctx.tool) or CAPABILITY_POLICY.get(capability)
    decision = base.decision
    risk = base.risk
    reason = base.reason
    ask = base.approval_required

    if policy == PermissionDecision.ALLOW and risk == RiskLevel.LOW and decision != PermissionDecision.BLOCK:
        decision = PermissionDecision.ALLOW
        ask = False
        reason = "Capability policy allows drafting / low-risk use"
    if policy == PermissionDecision.ASK and decision == PermissionDecision.ALLOW:
        decision = PermissionDecision.ASK
        ask = True
        reason = "Capability policy requires approval"
    if capability in {"payment.execute", "social.delete", "filesystem.delete", "calling.start"}:
        decision = PermissionDecision.ASK
        ask = True
        risk = RiskLevel.HIGH
        reason = "High-risk capability always requires approval"

    return GuardianResult(
        decision,
        risk,
        reason,
        ask,
        capability=capability,
        biometric_required=ctx.biometric_required or capability == "payment.execute",
    )
