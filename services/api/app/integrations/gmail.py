"""Gmail connector. Tokens are vaulted. Status is never faked as connected."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from app.config import settings
from app.models.enums import ConnectionStatus
from app.models.tables import Connection, SecretRecord
from app.security.vault import decrypt_secret, encrypt_secret

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
SCOPES = " ".join(
    [
        "openid",
        "email",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
    ]
)


def google_oauth_configured() -> bool:
    return bool((settings.google_client_id or "").strip() and (settings.google_client_secret or "").strip())


def authorize_url(state: str) -> str | None:
    if not google_oauth_configured():
        return None
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_oauth_redirect,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH}?{query}"


def _bundle(access_token: str, refresh_token: str | None = None, expires_in: int | None = None) -> str:
    expiry = None
    if expires_in:
        expiry = (datetime.now(UTC) + timedelta(seconds=int(expires_in) - 60)).isoformat()
    return json.dumps({"access_token": access_token, "refresh_token": refresh_token or "", "expiry": expiry})


def _parse_bundle(raw: str) -> dict[str, str]:
    raw = (raw or "").strip()
    if raw.startswith("{"):
        data = json.loads(raw)
        return {
            "access_token": str(data.get("access_token") or ""),
            "refresh_token": str(data.get("refresh_token") or ""),
            "expiry": str(data.get("expiry") or ""),
        }
    return {"access_token": raw, "refresh_token": "", "expiry": ""}


async def exchange_code(code: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any] | None:
    if not google_oauth_configured():
        return None
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_oauth_redirect,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code >= 400:
            return None
        payload = response.json()
        if not payload.get("access_token"):
            return None
        return payload
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()


async def _refresh(refresh_token: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any] | None:
    if not google_oauth_configured() or not refresh_token:
        return None
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            GOOGLE_TOKEN,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code >= 400:
            return None
        payload = response.json()
        if not payload.get("access_token"):
            return None
        payload.setdefault("refresh_token", refresh_token)
        return payload
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()


async def load_stored_gmail_token(db, user_id: str) -> str | None:
    row = (
        await db.execute(select(Connection).where(Connection.user_id == user_id, Connection.provider == "gmail"))
    ).scalar_one_or_none()
    if not row or row.status != ConnectionStatus.CONNECTED.value or not row.token_handle:
        return None
    secret = (await db.execute(select(SecretRecord).where(SecretRecord.handle == row.token_handle))).scalar_one_or_none()
    if not secret:
        return None
    try:
        parsed = _parse_bundle(decrypt_secret(secret.encrypted_value))
    except ValueError:
        return None
    access = parsed["access_token"]
    expiry = parsed["expiry"]
    expired = False
    if expiry:
        try:
            expired = datetime.fromisoformat(expiry) <= datetime.now(UTC)
        except ValueError:
            expired = False
    if expired and parsed["refresh_token"]:
        refreshed = await _refresh(parsed["refresh_token"])
        if refreshed and refreshed.get("access_token"):
            secret.encrypted_value = encrypt_secret(
                _bundle(refreshed["access_token"], refreshed.get("refresh_token") or parsed["refresh_token"], refreshed.get("expires_in"))
            )
            await db.commit()
            return refreshed["access_token"]
        return None
    return access or None


def encode_token_bundle(access_token: str, refresh_token: str | None = None, expires_in: int | None = None) -> str:
    return _bundle(access_token, refresh_token, expires_in)


async def gmail_whoami(token: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any] | None:
    token = (token or "").strip()
    if not token:
        return None
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.get(
            f"{GMAIL_API}/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            return None
        data = response.json()
        email = data.get("emailAddress")
        if not email:
            return None
        return {"email": email, "messages_total": data.get("messagesTotal")}
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _header_map(payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in (payload.get("payload") or {}).get("headers") or []:
        name = str(item.get("name") or "")
        if name.lower() in {"from", "to", "subject", "date"}:
            out[name.lower()] = str(item.get("value") or "")
    return out


async def gmail_list(token: str, *, query: str | None = None, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    identity = await gmail_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Gmail token is invalid"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        params: dict[str, Any] = {"maxResults": 8}
        if query:
            params["q"] = query
        listed = await http.get(f"{GMAIL_API}/users/me/messages", headers=_headers(token), params=params)
        if listed.status_code != 200:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Gmail API {listed.status_code}"}
        ids = [row.get("id") for row in (listed.json().get("messages") or []) if row.get("id")]
        messages = []
        for message_id in ids[:8]:
            detail = await http.get(
                f"{GMAIL_API}/users/me/messages/{message_id}",
                headers=_headers(token),
                params={"format": "metadata", "metadataHeaders": ["From", "To", "Subject", "Date"]},
            )
            if detail.status_code != 200:
                continue
            body = detail.json()
            headers = _header_map(body)
            messages.append(
                {
                    "id": message_id,
                    "from": headers.get("from", ""),
                    "subject": headers.get("subject", ""),
                    "date": headers.get("date", ""),
                    "snippet": (body.get("snippet") or "")[:240],
                }
            )
        return {"success": True, "data": {"account": identity["email"], "messages": messages, "query": query}}
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


async def gmail_read(token: str, message_id: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    if not message_id:
        return {"success": False, "error_code": "ACTION_FAILED", "error": "Missing message id"}
    identity = await gmail_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Gmail token is invalid"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        detail = await http.get(
            f"{GMAIL_API}/users/me/messages/{message_id}",
            headers=_headers(token),
            params={"format": "full"},
        )
        if detail.status_code != 200:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Gmail API {detail.status_code}"}
        body = detail.json()
        headers = _header_map(body)
        return {
            "success": True,
            "data": {
                "id": message_id,
                "account": identity["email"],
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "snippet": (body.get("snippet") or "")[:800],
            },
        }
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


def _raw_message(to: str, subject: str, body: str) -> str:
    message = MIMEText(body or "")
    message["to"] = to
    message["subject"] = subject or ""
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8").rstrip("=")
    return encoded


async def gmail_draft(token: str, *, to: str, subject: str, body: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    if not to:
        return {"success": False, "error_code": "ACTION_FAILED", "error": "Missing recipient"}
    identity = await gmail_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Gmail token is invalid"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            f"{GMAIL_API}/users/me/drafts",
            headers=_headers(token),
            json={"message": {"raw": _raw_message(to, subject, body)}},
        )
        if response.status_code not in {200, 201}:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Gmail API {response.status_code}"}
        data = response.json()
        return {"success": True, "data": {"draft_id": data.get("id"), "to": to, "subject": subject, "account": identity["email"]}}
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


async def gmail_send(token: str, *, to: str, subject: str, body: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    if not to:
        return {"success": False, "error_code": "ACTION_FAILED", "error": "Missing recipient"}
    identity = await gmail_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Gmail token is invalid"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            f"{GMAIL_API}/users/me/messages/send",
            headers=_headers(token),
            json={"raw": _raw_message(to, subject, body)},
        )
        if response.status_code not in {200, 201, 202}:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Gmail API {response.status_code}"}
        data = response.json()
        return {"success": True, "data": {"id": data.get("id"), "to": to, "subject": subject, "account": identity["email"]}}
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()
