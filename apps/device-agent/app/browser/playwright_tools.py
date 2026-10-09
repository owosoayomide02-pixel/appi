from __future__ import annotations

from typing import Any

_browser = None
_page = None
_killed = False


def set_killed(active: bool) -> None:
    global _killed
    _killed = active


async def close() -> None:
    global _browser, _page
    if _browser is not None:
        try:
            await _browser.close()
        except Exception:
            pass
    _browser = None
    _page = None


def _unavailable(reason: str) -> dict[str, Any]:
    return {"success": False, "error": reason, "verification_required": True}


async def execute(tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    global _browser, _page
    if _killed:
        return _unavailable("Kill switch is active")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return _unavailable("Playwright is not installed on this device")

    try:
        if tool == "browser.open_browser" or _browser is None:
            pw = await async_playwright().start()
            _browser = await pw.chromium.launch(headless=False)
            _page = await _browser.new_page()
            if tool == "browser.open_browser":
                return {"success": True, "data": {"open": True}, "verification_required": True}

        assert _page is not None
        if tool == "browser.open_url":
            url = payload.get("url") or ""
            if not url.startswith("http://") and not url.startswith("https://"):
                return _unavailable("Only http(s) URLs are allowed")
            await _page.goto(url, wait_until="domcontentloaded")
            text = await _page.inner_text("body")
            lowered = text.lower()
            return {
                "success": True,
                "data": {
                    "url": _page.url,
                    "text": text[:8000],
                    "captcha_required": "captcha" in lowered,
                    "mfa_required": any(token in lowered for token in ("two-factor", "2fa", "authenticator", "verification code")),
                },
                "verification_required": True,
            }
        if tool == "browser.read_page":
            text = await _page.inner_text("body")
            return {"success": True, "data": {"url": _page.url, "text": text[:12000]}, "verification_required": True}
        if tool == "browser.screenshot":
            image = await _page.screenshot(full_page=False)
            return {"success": True, "data": {"url": _page.url, "bytes": len(image)}, "verification_required": True}
        if tool == "browser.click":
            await _page.click(payload["selector"])
            return {"success": True, "data": {"url": _page.url, "text": (await _page.inner_text("body"))[:4000]}, "verification_required": True}
        if tool == "browser.type":
            if payload.get("contains_credentials") or payload.get("contains_payment"):
                return _unavailable("Credential/payment typing must be approved and explicitly confirmed")
            await _page.fill(payload["selector"], payload.get("text") or "")
            return {"success": True, "data": {"url": _page.url}, "verification_required": True}
        if tool == "browser.select":
            await _page.select_option(payload["selector"], payload.get("text") or payload.get("value"))
            return {"success": True, "data": {"url": _page.url}, "verification_required": True}
        if tool == "browser.scroll":
            await _page.mouse.wheel(0, int(payload.get("delta") or 800))
            return {"success": True, "data": {"url": _page.url}, "verification_required": True}
        if tool == "browser.upload_file":
            await _page.set_input_files(payload["selector"], payload["path"])
            return {"success": True, "data": {"url": _page.url}, "verification_required": True}
        if tool == "browser.download_file":
            return _unavailable("Download must be user-approved; automatic download is not enabled in V0.1")
        return _unavailable(f"Unknown browser tool: {tool}")
    except Exception as exc:
        return _unavailable(str(exc))


BLOCKED_LOGIN_HOSTS = (
    "paypal.",
    "paystack.",
    "stripe.",
    "bank",
    "wellsfargo.",
    "chase.com",
    "citi.com",
    "gtbank.",
    "opay.",
    "kuda.",
    "coinbase.",
    "binance.",
)

EMAIL_SELECTORS = (
    "input[type='email']",
    "input[name='email']",
    "input[name='username']",
    "input[autocomplete='username']",
    "input[id='email']",
    "input[id='username']",
)
PASSWORD_SELECTORS = (
    "input[type='password']",
    "input[name='password']",
    "input[autocomplete='current-password']",
    "input[id='password']",
)


def _host_blocked(url: str) -> bool:
    lowered = (url or "").lower()
    return any(token in lowered for token in BLOCKED_LOGIN_HOSTS)


async def _fill_first(page, selectors: tuple[str, ...], value: str) -> bool:
    for selector in selectors:
        loc = page.locator(selector).first
        try:
            if await loc.count():
                await loc.fill(value)
                return True
        except Exception:
            continue
    return False


async def login_with_vault(payload: dict[str, Any]) -> dict[str, Any]:
    from app.desktop.handoff import LOGIN, normalize_platform
    from app.secrets_vault import load_login, status

    creds = load_login()
    if not creds:
        return {
            "success": False,
            "error": "No login vault yet. Run: Appi.exe vault set",
            "error_code": "VAULT_EMPTY",
            "verification_required": True,
        }
    service = normalize_platform(payload.get("service") or payload.get("app") or payload.get("platform") or "")
    target = LOGIN.get(service)
    if not target:
        return {
            "success": False,
            "error": "Name a site in the allow-list (Gmail, GitHub, Instagram, Facebook, X, LinkedIn, WhatsApp).",
            "error_code": "ACTION_FAILED",
            "verification_required": True,
        }
    if _host_blocked(target["url"]):
        return {
            "success": False,
            "error": "Bank and payment logins stay with you. Appi will not type those passwords.",
            "error_code": "CAPABILITY_UNAVAILABLE",
            "verification_required": True,
        }
    opened = await execute("browser.open_url", {"url": target["url"]})
    if not opened.get("success"):
        return opened
    assert _page is not None
    if _host_blocked(_page.url):
        return {
            "success": False,
            "error": "This page looks like a bank or payment login. Appi stopped.",
            "error_code": "CAPABILITY_UNAVAILABLE",
            "verification_required": True,
        }
    filled_email = await _fill_first(_page, EMAIL_SELECTORS, creds["email"])
    filled_password = await _fill_first(_page, PASSWORD_SELECTORS, creds["password"])
    submitted = False
    for selector in ("button[type='submit']", "input[type='submit']"):
        loc = _page.locator(selector).first
        try:
            if await loc.count():
                await loc.click()
                submitted = True
                break
        except Exception:
            continue
    await _page.wait_for_timeout(1200)
    body = (await _page.inner_text("body")).lower()
    mfa = any(token in body for token in ("two-factor", "2fa", "authenticator", "verification code", "approve this login"))
    captcha = "captcha" in body
    return {
        "success": True,
        "data": {
            "service": service,
            "url": _page.url,
            "filled_email": filled_email,
            "filled_password": filled_password,
            "submitted": submitted,
            "mfa_required": mfa,
            "captcha_required": captcha,
            "typed_password": False,
            "password_sent_to_model": False,
            "vault": status(),
            "next_step": "Complete MFA or CAPTCHA yourself if the site asks. Appi did not send your password to the chat.",
        },
        "verification_required": True,
    }
