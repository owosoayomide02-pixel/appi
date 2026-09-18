"""GitHub connector. Tokens are vaulted. Status is never faked as connected."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.models.enums import ConnectionStatus
from app.models.tables import Connection, SecretRecord
from app.security.vault import decrypt_secret


GITHUB_API = "https://api.github.com"
GITHUB_LOGIN = "https://github.com/login"
DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
SCOPES = "read:user repo"


def github_oauth_configured() -> bool:
    return bool((settings.github_client_id or "").strip())


async def load_stored_token(db, user_id: str) -> str | None:
    from sqlalchemy import select

    row = (
        await db.execute(select(Connection).where(Connection.user_id == user_id, Connection.provider == "github"))
    ).scalar_one_or_none()
    if not row or row.status != ConnectionStatus.CONNECTED.value or not row.token_handle:
        return None
    secret = (await db.execute(select(SecretRecord).where(SecretRecord.handle == row.token_handle))).scalar_one_or_none()
    if not secret:
        return None
    try:
        return decrypt_secret(secret.encrypted_value)
    except ValueError:
        return None


async def github_whoami(token: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any] | None:
    token = (token or "").strip()
    if not token:
        return None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Appi",
    }
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.get(f"{GITHUB_API}/user", headers=headers)
        if response.status_code != 200:
            return None
        data = response.json()
        login = data.get("login")
        if not login:
            return None
        return {"login": login, "id": data.get("id"), "name": data.get("name")}
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()


async def github_list_repos(token: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    identity = await github_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "GitHub token is invalid"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Appi",
    }
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.get(f"{GITHUB_API}/user/repos", headers=headers, params={"per_page": 20, "sort": "updated"})
        if response.status_code != 200:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"GitHub API {response.status_code}"}
        repos = [{"name": r.get("full_name"), "private": r.get("private"), "url": r.get("html_url")} for r in response.json()]
        return {"success": True, "data": {"user": identity, "repos": repos}}
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


async def start_device_flow(*, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    if not github_oauth_configured():
        return {"ok": False, "error_code": "CONNECTOR_NOT_CONNECTED", "error": "GITHUB_CLIENT_ID is not configured"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            f"{GITHUB_LOGIN}/device/code",
            headers={"Accept": "application/json"},
            data={"client_id": settings.github_client_id, "scope": SCOPES},
        )
        if response.status_code >= 400:
            return {"ok": False, "error_code": "ACTION_FAILED", "error": response.text[:400]}
        payload = response.json()
        return {
            "ok": True,
            "user_code": payload.get("user_code"),
            "verification_uri": payload.get("verification_uri") or "https://github.com/login/device",
            "device_code": payload.get("device_code"),
            "expires_in": payload.get("expires_in"),
            "interval": payload.get("interval") or 5,
        }
    except Exception as exc:
        return {"ok": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


async def poll_device_flow(device_code: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    if not github_oauth_configured():
        return {"ok": False, "status": "error", "error_code": "CONNECTOR_NOT_CONNECTED"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        data: dict[str, str] = {
            "client_id": settings.github_client_id,
            "device_code": device_code,
            "grant_type": DEVICE_GRANT,
        }
        if settings.github_client_secret:
            data["client_secret"] = settings.github_client_secret
        response = await http.post(
            f"{GITHUB_LOGIN}/oauth/access_token",
            headers={"Accept": "application/json"},
            data=data,
        )
        payload = response.json()
        if payload.get("access_token"):
            return {"ok": True, "status": "connected", "access_token": payload["access_token"]}
        err = payload.get("error") or "pending"
        if err in {"authorization_pending", "slow_down"}:
            return {"ok": True, "status": "pending", "error": err}
        return {"ok": False, "status": "error", "error": err, "error_code": "AUTHENTICATION_REQUIRED"}
    except Exception as exc:
        return {"ok": False, "status": "error", "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


def authorize_url(state: str) -> str | None:
    if not github_oauth_configured():
        return None
    from urllib.parse import urlencode

    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_oauth_redirect,
            "scope": SCOPES,
            "state": state,
        }
    )
    return f"{GITHUB_LOGIN}/oauth/authorize?{query}"


async def exchange_code(code: str, *, client: httpx.AsyncClient | None = None) -> str | None:
    if not github_oauth_configured() or not settings.github_client_secret:
        return None
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            f"{GITHUB_LOGIN}/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_oauth_redirect,
            },
        )
        payload = response.json()
        return payload.get("access_token")
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()
