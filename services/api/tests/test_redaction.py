from app.audit.redaction import REDACTED, redact_text, redact_value


def test_redacts_bearer_tokens():
    assert REDACTED in redact_text("Authorization: Bearer abcdefghijklmnop")


def test_redacts_openai_style_keys():
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in redact_text("key=sk-abcdefghijklmnopqrstuvwxyz123456")


def test_keeps_secret_handles():
    handle = "secret://github/token/main"
    assert redact_value(handle) == handle


def test_redacts_password_fields():
    out = redact_value({"password": "hunter2", "note": "ok"})
    assert out["password"] == REDACTED
    assert out["note"] == "ok"
