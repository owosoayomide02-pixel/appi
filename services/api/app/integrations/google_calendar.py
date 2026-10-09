"""Google Calendar connector. Tokens are vaulted. Status is never faked as connected.

Gmail and Contacts stay disconnected. This module does not request those scopes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from app.config import settings
from app.integrations.gmail import google_oauth_configured
from app.models.enums import ConnectionStatus
from app.models.tables import Connection, SecretRecord
from app.security.vault import decrypt_secret, encrypt_secret

CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
SCOPES = " ".join(
    [
        "openid",
        "email",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]
)


def authorize_url(state: str) -> str | None:
    if not google_oauth_configured():
        return None
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_calendar_oauth_redirect,
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


def encode_calendar_token_bundle(access_token: str, refresh_token: str | None = None, expires_in: int | None = None) -> str:
    return _bundle(access_token, refresh_token, expires_in)


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
                "redirect_uri": settings.google_calendar_oauth_redirect,
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


async def load_stored_calendar_token(db, user_id: str) -> str | None:
    row = (
        await db.execute(select(Connection).where(Connection.user_id == user_id, Connection.provider == "google_calendar"))
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


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


async def calendar_whoami(token: str, *, client: httpx.AsyncClient | None = None) -> dict[str, Any] | None:
    token = (token or "").strip()
    if not token:
        return None
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.get(
            f"{CALENDAR_API}/users/me/calendarList",
            headers=_headers(token),
            params={"maxResults": 8, "minAccessRole": "reader"},
        )
        if response.status_code != 200:
            return None
        items = response.json().get("items") or []
        primary = next((row for row in items if row.get("primary")), items[0] if items else None)
        if not primary:
            return None
        account = str(primary.get("id") or primary.get("summary") or "").strip()
        if not account:
            return None
        return {"email": account, "calendar_id": str(primary.get("id") or "primary"), "summary": primary.get("summary")}
    except Exception:
        return None
    finally:
        if own:
            await http.aclose()


def _event_when(event: dict[str, Any]) -> str:
    start = event.get("start") or {}
    return str(start.get("dateTime") or start.get("date") or "")


async def calendar_list(token: str, *, query: str | None = None, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    identity = await calendar_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Calendar token is invalid"}
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        params: dict[str, Any] = {
            "maxResults": 8,
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if query:
            params["q"] = query
        listed = await http.get(
            f"{CALENDAR_API}/calendars/primary/events",
            headers=_headers(token),
            params=params,
        )
        if listed.status_code != 200:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Calendar API {listed.status_code}"}
        events = []
        for row in listed.json().get("items") or []:
            events.append(
                {
                    "id": row.get("id"),
                    "summary": row.get("summary") or "(no title)",
                    "start": _event_when(row),
                    "html_link": row.get("htmlLink") or "",
                }
            )
        return {"success": True, "data": {"account": identity["email"], "events": events, "query": query}}
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()


async def calendar_create(
    token: str,
    *,
    summary: str,
    start: str,
    end: str | None = None,
    description: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    if not (summary or "").strip():
        return {"success": False, "error_code": "ACTION_FAILED", "error": "Missing event title"}
    if not (start or "").strip():
        return {"success": False, "error_code": "ACTION_FAILED", "error": "Missing event start time"}
    identity = await calendar_whoami(token, client=client)
    if not identity:
        return {"success": False, "error_code": "AUTHENTICATION_REQUIRED", "error": "Calendar token is invalid"}
    end = (end or "").strip() or start
    body: dict[str, Any] = {
        "summary": summary.strip(),
        "start": {"dateTime": start, "timeZone": "UTC"} if "T" in start else {"date": start},
        "end": {"dateTime": end, "timeZone": "UTC"} if "T" in end else {"date": end},
    }
    if description:
        body["description"] = description
    own = client is None
    http = client or httpx.AsyncClient(timeout=12)
    try:
        response = await http.post(
            f"{CALENDAR_API}/calendars/primary/events",
            headers=_headers(token),
            json=body,
        )
        if response.status_code not in {200, 201}:
            return {"success": False, "error_code": "ACTION_FAILED", "error": f"Calendar API {response.status_code}"}
        data = response.json()
        event_id = data.get("id")
        if not event_id:
            return {"success": False, "error_code": "ACTION_FAILED", "error": "Calendar did not return an event id"}
        return {
            "success": True,
            "data": {
                "id": event_id,
                "summary": data.get("summary") or summary,
                "start": _event_when(data),
                "account": identity["email"],
                "html_link": data.get("htmlLink") or "",
            },
        }
    except Exception as exc:
        return {"success": False, "error_code": "NETWORK_REQUIRED", "error": str(exc)}
    finally:
        if own:
            await http.aclose()
