from app.guardian.engine import GuardianContext, guard
from app.models.enums import PermissionDecision
from app.runtime.capabilities import CAPABILITY_UNAVAILABLE, device_has_capability, default_capabilities
from app.permissions.engine import ActionContext, decide


def test_windows_read_is_allowed_when_filesystem_present():
    caps = default_capabilities("windows")
    result = guard(
        GuardianContext(
            tool="files.read_file",
            action="files.read_file",
            device_capabilities=caps,
            platform="windows",
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ALLOW


def test_write_asks_without_grant():
    caps = default_capabilities("windows")
    result = guard(
        GuardianContext(
            tool="files.write_file",
            action="files.write_file",
            device_capabilities=caps,
            platform="windows",
            target=r"C:\Users\User\Projects\app\a.ts",
        )
    )
    assert result.decision == PermissionDecision.ASK
    assert result.unavailable is False


def test_payment_execute_requires_connector():
    caps = default_capabilities("windows")
    result = guard(
        GuardianContext(
            tool="payment.execute",
            action="payment.execute",
            device_capabilities=caps,
            platform="windows",
            amount=25000,
            currency="NGN",
        )
    )
    assert result.unavailable is True
    assert result.error_code == "CONNECTOR_NOT_CONNECTED"


def test_android_filesystem_unavailable():
    caps = default_capabilities("android")
    result = guard(
        GuardianContext(
            tool="files.read_file",
            action="files.read_file",
            device_capabilities=caps,
            platform="android",
        )
    )
    assert result.error_code == CAPABILITY_UNAVAILABLE


def test_social_publish_asks_if_capability_forced_for_policy_check():
    from app.guardian.engine import CAPABILITY_POLICY
    from app.models.enums import PermissionDecision as PD

    assert CAPABILITY_POLICY["social.publish"] == PD.ASK
    assert CAPABILITY_POLICY["social.draft"] == PD.ALLOW
    assert CAPABILITY_POLICY["social.delete"] == PD.ASK


def test_social_draft_is_allowed_on_windows():
    caps = default_capabilities("windows")
    result = guard(
        GuardianContext(
            tool="social.draft",
            action="social.draft",
            device_capabilities=caps,
            platform="windows",
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ALLOW
    assert caps["social.draft"] is True
    assert caps["social.publish"] is False


def test_device_has_capability_group_fallback():
    assert device_has_capability({"filesystem": True}, "filesystem.read") is True
    assert device_has_capability({"filesystem": False}, "filesystem.read") is False
    assert device_has_capability({"filesystem.read": True, "filesystem": False}, "filesystem.read") is True


def test_sanitize_cannot_enable_unimplemented_capabilities():
    from app.runtime.capabilities import sanitize_reported_capabilities

    cleaned = sanitize_reported_capabilities(
        "windows",
        {"filesystem": True, "payment.execute": True, "payments": True, "contacts": True},
    )
    assert cleaned["filesystem"] is True
    assert cleaned["payment.execute"] is False
    assert cleaned["payments"] is False
    assert cleaned["contacts"] is False


def test_delete_still_asks_on_engine():
    result = decide(ActionContext(tool="files.delete_file", action="files.delete_file"))
    assert result.decision == PermissionDecision.ASK
