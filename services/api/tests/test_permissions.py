from app.models.enums import PermissionDecision, RiskLevel
from app.permissions.engine import ActionContext, decide


def test_low_risk_read_is_allowed():
    result = decide(ActionContext(tool="files.read_file", action="files.read_file", target=r"C:\Users\User\Projects\app"))
    assert result.decision == PermissionDecision.ALLOW
    assert result.risk == RiskLevel.LOW


def test_delete_always_asks():
    result = decide(ActionContext(tool="files.delete_file", action="files.delete_file", target=r"C:\Users\User\Projects\app\a.txt"))
    assert result.decision == PermissionDecision.ASK
    assert result.risk == RiskLevel.HIGH
    assert result.approval_required


def test_forbidden_actions_are_blocked():
    result = decide(ActionContext(tool="files.read_file", action="bypass_permissions"))
    assert result.decision == PermissionDecision.BLOCK


def test_previous_denial_is_blocked():
    result = decide(
        ActionContext(
            tool="terminal.run_command",
            action="terminal.run_command",
            previously_denied=True,
        )
    )
    assert result.decision == PermissionDecision.BLOCK


def test_kill_switch_blocks_everything():
    result = decide(ActionContext(tool="files.read_file", action="files.read_file", kill_switch_active=True))
    assert result.decision == PermissionDecision.BLOCK


def test_user_policy_can_block_terminal():
    result = decide(
        ActionContext(
            tool="terminal.run_command",
            action="terminal.run_command",
            user_policy={"run_terminal": "BLOCK"},
        )
    )
    assert result.decision == PermissionDecision.BLOCK


def test_medium_risk_asks_without_grant():
    result = decide(ActionContext(tool="files.write_file", action="files.write_file", target=r"C:\p\a.ts"))
    assert result.decision == PermissionDecision.ASK


def test_matching_grant_allows_write():
    result = decide(
        ActionContext(
            tool="files.write_file",
            action="files.write_file",
            target=r"C:\Users\User\Projects\app\file.ts",
            grants=[
                {
                    "resource": "files",
                    "scope": r"C:\Users\User\Projects\app",
                    "actions": ["write", "write_file"],
                    "requires_confirmation": False,
                }
            ],
        )
    )
    assert result.decision == PermissionDecision.ALLOW


def test_credentials_form_always_asks():
    result = decide(
        ActionContext(
            tool="browser.type",
            action="browser.type",
            contains_credentials=True,
        )
    )
    assert result.decision == PermissionDecision.ASK
    assert result.risk == RiskLevel.HIGH


def test_unknown_domain_asks():
    result = decide(
        ActionContext(
            tool="browser.open_url",
            action="browser.open_url",
            domain="unknown.example",
            domain_policy="ask",
        )
    )
    assert result.decision == PermissionDecision.ASK
