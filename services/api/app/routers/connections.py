from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.integrations.catalog import CATEGORIES, CONNECTORS
from app.integrations.gmail import (
    authorize_url as gmail_authorize_url,
    encode_token_bundle,
    exchange_code as gmail_exchange_code,
    gmail_whoami,
    google_oauth_configured,
    load_stored_gmail_token,
)
from app.integrations.google_calendar import (
    authorize_url as calendar_authorize_url,
    calendar_whoami,
    encode_calendar_token_bundle,
    exchange_code as calendar_exchange_code,
)
from app.integrations.github import (
    authorize_url,
    exchange_code,
    github_oauth_configured,
    github_whoami,
    load_stored_token,
    poll_device_flow,
    start_device_flow,
)
from app.integrations.supabase import ping_supabase, supabase_configured
from app.models.enums import ConnectionStatus
from app.models.tables import Connection, SecretRecord, User, new_id
from app.security.vault import encrypt_secret, make_handle, random_token

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])


async def _ensure_catalog(db: AsyncSession, user_id: str) -> dict[str, Connection]:
    rows = (await db.execute(select(Connection).where(Connection.user_id == user_id))).scalars().all()
    by_id = {r.provider: r for r in rows}
    dirty = False
    for meta in CONNECTORS:
        row = by_id.get(meta["id"])
        if row is None:
            row = Connection(
                id=new_id(),
                user_id=user_id,
                provider=meta["id"],
                category=meta["category"],
                status=meta["status"],
            )
            db.add(row)
            by_id[meta["id"]] = row
            dirty = True
        elif not row.category:
            row.category = meta["category"]
            dirty = True
    if dirty:
        await db.commit()
    return by_id


async def _sync_env_connectors(db: AsyncSession, user_id: str, by_id: dict[str, Connection]) -> None:
    row = by_id.get("supabase")
    if row is None:
        return
    if not supabase_configured():
        if row.status == "connected":
            row.status = "not_connected"
            row.token_handle = None
            await db.commit()
        return
    reachable = await ping_supabase()
    handle = make_handle("supabase", "service")
    if reachable:
        row.status = "connected"
        row.token_handle = handle
        existing = (await db.execute(select(SecretRecord).where(SecretRecord.handle == handle))).scalar_one_or_none()
        ciphertext = encrypt_secret(settings.supabase_service_role_key or settings.supabase_anon_key)
        if existing is None:
            db.add(SecretRecord(id=new_id(), user_id=user_id, handle=handle, encrypted_value=ciphertext))
        else:
            existing.encrypted_value = ciphertext
    else:
        row.status = "not_connected"
        row.token_handle = None
    await db.commit()


async def github_token_for_user(db: AsyncSession, user_id: str) -> str | None:
    return await load_stored_token(db, user_id)


async def github_is_connected(db: AsyncSession, user_id: str) -> bool:
    return bool(await github_token_for_user(db, user_id))


async def _store_github_token(db: AsyncSession, user: User, token: str) -> dict[str, Any]:
    identity = await github_whoami(token)
    if not identity:
        raise HTTPException(status_code=400, detail="GitHub token was rejected. Appi did not mark GitHub as connected.")
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    handle = make_handle("github", "oauth")
    ciphertext = encrypt_secret(token)
    existing = (await db.execute(select(SecretRecord).where(SecretRecord.handle == handle))).scalar_one_or_none()
    if existing is None:
        db.add(SecretRecord(id=new_id(), user_id=user.id, handle=handle, encrypted_value=ciphertext))
    else:
        existing.encrypted_value = ciphertext
    row.status = ConnectionStatus.CONNECTED.value
    row.token_handle = handle
    meta = dict(row.metadata_json or {})
    meta.pop("device_code", None)
    meta["login"] = identity["login"]
    meta["github_id"] = identity.get("id")
    row.metadata_json = meta
    await db.commit()
    return identity


@router.get("")
async def list_connections(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    by_id = await _ensure_catalog(db, user.id)
    await _sync_env_connectors(db, user.id, by_id)
    out = []
    for meta in CONNECTORS:
        row = by_id.get(meta["id"])
        status = row.status if row else meta["status"]
        if status == "connected" and not (row and row.token_handle):
            status = "not_connected"
        item: dict[str, Any] = {
            "provider": meta["id"],
            "name": meta["name"],
            "category": meta["category"],
            "oauth": meta["oauth"],
            "status": status,
            "connected": status == "connected",
            "oauth_ready": False,
            "account": None,
        }
        if meta["id"] == "github":
            item["oauth_ready"] = github_oauth_configured()
            item["account"] = (row.metadata_json or {}).get("login") if row else None
        if meta["id"] == "gmail":
            item["oauth_ready"] = google_oauth_configured()
            item["account"] = (row.metadata_json or {}).get("email") if row else None
        if meta["id"] == "google_calendar":
            item["oauth_ready"] = google_oauth_configured()
            item["account"] = (row.metadata_json or {}).get("email") if row else None
        out.append(item)
    return out


@router.get("/categories")
async def list_categories() -> list[str]:
    return CATEGORIES


class GitHubTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=256)


@router.post("/github/token")
async def connect_github_token(
    payload: GitHubTokenIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    identity = await _store_github_token(db, user, payload.token.strip())
    return {"connected": True, "provider": "github", "login": identity["login"]}


@router.post("/github/oauth/device")
async def github_device_start(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    started = await start_device_flow()
    if not started.get("ok"):
        raise HTTPException(status_code=400, detail=started.get("error") or "GitHub OAuth is not configured")
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    meta = dict(row.metadata_json or {})
    meta["device_code"] = started["device_code"]
    row.metadata_json = meta
    await db.commit()
    return {
        "ok": True,
        "user_code": started["user_code"],
        "verification_uri": started["verification_uri"],
        "expires_in": started["expires_in"],
        "interval": started["interval"],
    }


@router.post("/github/oauth/device/poll")
async def github_device_poll(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    device_code = (row.metadata_json or {}).get("device_code")
    if not device_code:
        raise HTTPException(status_code=400, detail="No GitHub device login in progress")
    polled = await poll_device_flow(device_code)
    if polled.get("status") == "connected" and polled.get("access_token"):
        identity = await _store_github_token(db, user, polled["access_token"])
        return {"status": "connected", "login": identity["login"]}
    return {"status": polled.get("status") or "error", "error": polled.get("error")}


@router.get("/github/oauth/start")
async def github_oauth_start(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not github_oauth_configured():
        raise HTTPException(status_code=400, detail="GITHUB_CLIENT_ID is not configured")
    state = random_token(16)
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    meta = dict(row.metadata_json or {})
    meta["oauth_state"] = state
    row.metadata_json = meta
    await db.commit()
    url = authorize_url(state)
    if not url:
        raise HTTPException(status_code=400, detail="GitHub OAuth is not configured")
    return RedirectResponse(url)


@router.get("/github/oauth/callback")
async def github_oauth_callback(code: str = "", state: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    expected = (row.metadata_json or {}).get("oauth_state")
    if not code or not state or state != expected:
        raise HTTPException(status_code=400, detail="Invalid GitHub OAuth state")
    token = await exchange_code(code)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub did not return an access token")
    await _store_github_token(db, user, token)
    from app.config import settings

    return RedirectResponse(f"{settings.public_app_url}/connections?github=connected")


@router.delete("/github")
async def disconnect_github(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["github"]
    if row.token_handle:
        secret = (await db.execute(select(SecretRecord).where(SecretRecord.handle == row.token_handle))).scalar_one_or_none()
        if secret:
            await db.delete(secret)
    row.status = ConnectionStatus.NOT_CONNECTED.value
    row.token_handle = None
    row.metadata_json = {}
    await db.commit()
    return {"connected": False, "provider": "github"}


async def gmail_token_for_user(db: AsyncSession, user_id: str) -> str | None:
    return await load_stored_gmail_token(db, user_id)


async def _store_gmail_token(
    db: AsyncSession,
    user: User,
    access_token: str,
    *,
    refresh_token: str | None = None,
    expires_in: int | None = None,
) -> dict[str, Any]:
    identity = await gmail_whoami(access_token)
    if not identity:
        raise HTTPException(status_code=400, detail="Gmail token was rejected. Appi did not mark Gmail as connected.")
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["gmail"]
    handle = make_handle("gmail", "oauth")
    ciphertext = encrypt_secret(encode_token_bundle(access_token, refresh_token, expires_in))
    existing = (await db.execute(select(SecretRecord).where(SecretRecord.handle == handle))).scalar_one_or_none()
    if existing is None:
        db.add(SecretRecord(id=new_id(), user_id=user.id, handle=handle, encrypted_value=ciphertext))
    else:
        existing.encrypted_value = ciphertext
    row.status = ConnectionStatus.CONNECTED.value
    row.token_handle = handle
    meta = dict(row.metadata_json or {})
    meta.pop("oauth_state", None)
    meta["email"] = identity["email"]
    row.metadata_json = meta
    await db.commit()
    return identity


class GmailTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=4096)


@router.post("/gmail/token")
async def connect_gmail_token(
    payload: GmailTokenIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    identity = await _store_gmail_token(db, user, payload.token.strip())
    return {"connected": True, "provider": "gmail", "email": identity["email"]}


@router.get("/gmail/oauth/start")
async def gmail_oauth_start(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not google_oauth_configured():
        raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are not configured")
    state = random_token(16)
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["gmail"]
    meta = dict(row.metadata_json or {})
    meta["oauth_state"] = state
    row.metadata_json = meta
    await db.commit()
    url = gmail_authorize_url(state)
    if not url:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    return RedirectResponse(url)


@router.get("/gmail/oauth/callback")
async def gmail_oauth_callback(code: str = "", state: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["gmail"]
    expected = (row.metadata_json or {}).get("oauth_state")
    if not code or not state or state != expected:
        raise HTTPException(status_code=400, detail="Invalid Gmail OAuth state")
    payload = await gmail_exchange_code(code)
    if not payload or not payload.get("access_token"):
        raise HTTPException(status_code=400, detail="Google did not return an access token")
    await _store_gmail_token(
        db,
        user,
        str(payload["access_token"]),
        refresh_token=payload.get("refresh_token"),
        expires_in=payload.get("expires_in"),
    )
    from app.config import settings

    return RedirectResponse(f"{settings.public_app_url}/connections?gmail=connected")


@router.delete("/gmail")
async def disconnect_gmail(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["gmail"]
    if row.token_handle:
        secret = (await db.execute(select(SecretRecord).where(SecretRecord.handle == row.token_handle))).scalar_one_or_none()
        if secret:
            await db.delete(secret)
    row.status = ConnectionStatus.NOT_CONNECTED.value
    row.token_handle = None
    row.metadata_json = {}
    await db.commit()
    return {"connected": False, "provider": "gmail"}


async def _store_calendar_token(
    db: AsyncSession,
    user: User,
    access_token: str,
    *,
    refresh_token: str | None = None,
    expires_in: int | None = None,
) -> dict[str, Any]:
    identity = await calendar_whoami(access_token)
    if not identity:
        raise HTTPException(status_code=400, detail="Calendar token was rejected. Appi did not mark Google Calendar as connected.")
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["google_calendar"]
    handle = make_handle("google_calendar", "oauth")
    ciphertext = encrypt_secret(encode_calendar_token_bundle(access_token, refresh_token, expires_in))
    existing = (await db.execute(select(SecretRecord).where(SecretRecord.handle == handle))).scalar_one_or_none()
    if existing is None:
        db.add(SecretRecord(id=new_id(), user_id=user.id, handle=handle, encrypted_value=ciphertext))
    else:
        existing.encrypted_value = ciphertext
    row.status = ConnectionStatus.CONNECTED.value
    row.token_handle = handle
    meta = dict(row.metadata_json or {})
    meta.pop("oauth_state", None)
    meta["email"] = identity["email"]
    row.metadata_json = meta
    await db.commit()
    return identity


class CalendarTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=4096)


@router.post("/google_calendar/token")
async def connect_calendar_token(
    payload: CalendarTokenIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    identity = await _store_calendar_token(db, user, payload.token.strip())
    return {"connected": True, "provider": "google_calendar", "email": identity["email"]}


@router.get("/google_calendar/oauth/start")
async def calendar_oauth_start(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not google_oauth_configured():
        raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are not configured")
    state = random_token(16)
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["google_calendar"]
    meta = dict(row.metadata_json or {})
    meta["oauth_state"] = state
    row.metadata_json = meta
    await db.commit()
    url = calendar_authorize_url(state)
    if not url:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    return RedirectResponse(url)


@router.get("/google_calendar/oauth/callback")
async def calendar_oauth_callback(code: str = "", state: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["google_calendar"]
    expected = (row.metadata_json or {}).get("oauth_state")
    if not code or not state or state != expected:
        raise HTTPException(status_code=400, detail="Invalid Google Calendar OAuth state")
    payload = await calendar_exchange_code(code)
    if not payload or not payload.get("access_token"):
        raise HTTPException(status_code=400, detail="Google did not return an access token")
    await _store_calendar_token(
        db,
        user,
        str(payload["access_token"]),
        refresh_token=payload.get("refresh_token"),
        expires_in=payload.get("expires_in"),
    )
    from app.config import settings

    return RedirectResponse(f"{settings.public_app_url}/connections?calendar=connected")


@router.delete("/google_calendar")
async def disconnect_calendar(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    by_id = await _ensure_catalog(db, user.id)
    row = by_id["google_calendar"]
    if row.token_handle:
        secret = (await db.execute(select(SecretRecord).where(SecretRecord.handle == row.token_handle))).scalar_one_or_none()
        if secret:
            await db.delete(secret)
    row.status = ConnectionStatus.NOT_CONNECTED.value
    row.token_handle = None
    row.metadata_json = {}
    await db.commit()
    return {"connected": False, "provider": "google_calendar"}
