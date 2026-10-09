from app.guardian.engine import CONNECTOR_NOT_CONNECTED, GuardianContext, guard
from app.models.enums import PermissionDecision
from app.providers.heuristic import heuristic_plan
from app.resolver.action import resolve_action
from app.runtime.capabilities import default_capabilities


def test_chrome_search_plan_uses_app_launch():
    plan = heuristic_plan("Open Chrome and search for FastAPI documentation")
    assert plan.steps[0].tool == "app.launch"
    assert "google.com/search" in plan.steps[0].input["url"]
    assert plan.steps[0].approval_required is True


def test_open_named_app_plan():
    plan = heuristic_plan("open Spotify")
    assert plan.steps[0].tool == "app.launch"
    assert plan.steps[0].input["app"].lower() == "spotify"
    calc = heuristic_plan("Appi, open calculator")
    assert calc.steps[0].tool == "app.launch"
    assert "calculator" in calc.steps[0].input["app"].lower()


def test_run_tests_plan_is_background():
    plan = heuristic_plan("Appi, open my project and run the tests.")
    assert plan.steps[0].tool == "project.run_tests"
    assert len(plan.steps) == 1


def test_delete_project_asks():
    plan = heuristic_plan("Appi, delete my project.")
    assert plan.steps[0].tool == "files.delete_file"
    caps = default_capabilities("windows")
    result = guard(
        GuardianContext(
            tool="files.delete_file",
            action="files.delete_file",
            device_capabilities=caps,
            platform="windows",
            target=r"C:\Users\User\Projects\app",
        )
    )
    assert result.decision == PermissionDecision.ASK
    assert result.unavailable is False


def test_transfer_without_connector():
    plan = heuristic_plan("Appi, transfer ₦50,000.")
    assert plan.steps[0].tool == "transfer.execute"
    result = guard(
        GuardianContext(
            tool="transfer.execute",
            action="transfer.execute",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            amount=50000,
            currency="NGN",
            connector_connected=False,
        )
    )
    assert result.error_code == CONNECTOR_NOT_CONNECTED
    assert result.unavailable is True


def test_voice_cannot_authenticate_payment_even_with_connector():
    result = guard(
        GuardianContext(
            tool="payment.execute",
            action="payment.execute",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            amount=500000,
            currency="NGN",
            connector_connected=True,
            voice_input=True,
        )
    )
    assert result.error_code == "AUTHENTICATION_REQUIRED"


def test_instagram_post_is_drafted_not_published():
    plan = heuristic_plan("Write an Instagram post about Appi helping Ayomide")
    assert plan.steps[0].tool == "social.draft"
    assert plan.steps[0].input["platform"] == "instagram"
    assert "Appi" in plan.steps[0].input["text"]
    assert plan.steps[0].approval_required is False


def test_login_uses_local_vault():
    plan = heuristic_plan("log in to Gmail")
    assert plan.steps[0].tool == "access.login"
    assert plan.steps[0].input["service"] == "gmail"
    assert "password" not in plan.steps[0].input


def test_resolver_instagram_asks():
    resolved = resolve_action("Post this picture on Instagram.")
    assert resolved.intent == "social.publish"
    assert resolved.service == "instagram"
    assert resolved.connector_available is False
    assert resolved.permission == "ASK"
