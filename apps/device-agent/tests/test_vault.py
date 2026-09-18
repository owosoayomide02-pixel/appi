from app.browser.playwright_tools import _host_blocked
from app.secrets_vault import clear_login, save_login, status


def test_vault_roundtrip_with_identity_protect(tmp_path, monkeypatch):
    from app import secrets_vault

    monkeypatch.setattr(secrets_vault, "vault_path", lambda: tmp_path / "login.vault")
    monkeypatch.setattr(secrets_vault, "_protect", lambda raw: raw)
    monkeypatch.setattr(secrets_vault, "_unprotect", lambda raw: raw)
    saved = save_login("ayomide@example.com", "not-for-the-model")
    assert saved["saved"] is True
    assert "not-for-the-model" not in str(saved)
    assert saved["model_can_read_password"] is False
    assert "***" in saved["email"]
    loaded = secrets_vault.load_login()
    assert loaded is not None
    assert loaded["password"] == "not-for-the-model"
    assert status()["model_can_read_password"] is False
    clear_login()
    assert secrets_vault.load_login() is None


def test_payment_hosts_are_blocked():
    assert _host_blocked("https://www.paypal.com/signin") is True
    assert _host_blocked("https://paystack.com/login") is True
    assert _host_blocked("https://www.instagram.com/accounts/login/") is False
