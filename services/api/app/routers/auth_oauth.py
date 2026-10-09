"""Account OAuth (sign in / sign up) for GitHub and Google.

Separate from /connections OAuth, which links tools after you already have an account.
"""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.integrations.catalog import CONNECTORS
from app.models.tables import Connection, User, UserPolicy, new_id
from app.security.passwords import hash_password
from app.security.tokens import create_access_token

router = APIRouter(prefix="/api/v1/auth/oauth", tags=["auth-oauth"])

# In-memory state for OAuth CSRF (fine for single-instance; multi-instance should use Redis).
_pending_states: dict[str, str] = {}

GITHUB_AUTH_SCOPES = "read:user user:email"
GOOGLE_AUTH_SCOPES = "openid email profile"


def _cookie_opts() -> dict[str, Any]:
    api_https = settings.public_api_url.startswith("https")
    return {
        "httponly": True,
        "samesite": "none" if api_https else "lax",
        "secure": api_https,
        "max_age": 60 * 60 * 24 * 7,
        "path": "/",
    }


def _github_auth_redirect() -> str:
    return (settings.github_auth_oauth_redirect or "").strip() or (
        f"{settings.public_api_url}/api/v1/auth/oauth/github/callback"
    )


def _google_auth_redirect() -> str:
    return (settings.google_auth_oauth_redirect or "").strip() or (
        f"{settings.public_api_url}/api/v1/auth/oauth/google/callback"
    )


def _seed_connections(user_id: str) -> list[Connection]:
    return [
        Connection(
            id=new_id(),
            user_id=user_id,
            provider=meta["id"],
            category=meta["category"],
            status=meta["status"],
        )
        for meta in CONNECTORS
    ]


async def _upsert_oauth_user(
    db: AsyncSession,
    *,
    provider: str,
    subject: str,
    email: str,
    display_name: str,
) -> User:
    email = email.lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail=f"{provider} did not provide an email")

    by_oauth = (
        await db.execute(
            select(User).where(User.oauth_provider == provider, User.oauth_subject == subject)
        )
    ).scalar_one_or_none()
    if by_oauth:
        return by_oauth

    by_email = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if by_email:
        by_email.oauth_provider = provider
        by_email.oauth_subject = subject
        if display_name and not by_email.display_name:
            by_email.display_name = display_name
        await db.commit()
        await db.refresh(by_email)
        return by_email

    user = User(
        id=new_id(),
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        display_name=display_name or email.split("@")[0],
        oauth_provider=provider,
        oauth_subject=subject,
    )
    db.add(user)
    db.add(UserPolicy(id=new_id(), user_id=user.id))
    for conn in _seed_connections(user.id):
        db.add(conn)
    await db.commit()
    await db.refresh(user)
    return user


def _finish_login(user: User) -> RedirectResponse:
    token = create_access_token(user.id)
    dest = "/app" if user.onboarding_completed else "/onboarding"
    redirect = RedirectResponse(
        f"{settings.public_app_url}{dest}?oauth=1&access_token={token}",
        status_code=302,
    )
    redirect.set_cookie("access_token", token, **_cookie_opts())
    return redirect


@router.get("/providers")
async def oauth_providers() -> dict[str, Any]:
    return {
        "github": bool((settings.github_client_id or "").strip() and (settings.github_client_secret or "").strip()),
        "google": bool((settings.google_client_id or "").strip() and (settings.google_client_secret or "").strip()),
    }


@router.get("/github/start")
async def github_auth_start() -> RedirectResponse:
    if not (settings.github_client_id or "").strip() or not (settings.github_client_secret or "").strip():
        raise HTTPException(status_code=400, detail="GitHub OAuth is not configured")
    state = secrets.token_urlsafe(24)
    _pending_states[state] = "github"
    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": _github_auth_redirect(),
            "scope": GITHUB_AUTH_SCOPES,
            "state": state,
            "allow_signup": "true",
        }
    )
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{query}")


@router.get("/github/callback")
async def github_auth_callback(
    code: str = "",
    state: str = "",
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if not code or not state or _pending_states.pop(state, None) != "github":
        raise HTTPException(status_code=400, detail="Invalid GitHub OAuth state")
    async with httpx.AsyncClient(timeout=15) as http:
        token_res = await http.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": _github_auth_redirect(),
            },
        )
        token_payload = token_res.json()
        access = token_payload.get("access_token")
        if not access:
            raise HTTPException(status_code=400, detail="GitHub did not return an access token")
        headers = {
            "Authorization": f"Bearer {access}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Appi",
        }
        user_res = await http.get("https://api.github.com/user", headers=headers)
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not read GitHub profile")
        profile = user_res.json()
        email = (profile.get("email") or "").strip()
        if not email:
            emails_res = await http.get("https://api.github.com/user/emails", headers=headers)
            if emails_res.status_code == 200:
                for row in emails_res.json():
                    if row.get("primary") and row.get("verified") and row.get("email"):
                        email = row["email"]
                        break
                if not email:
                    for row in emails_res.json():
                        if row.get("verified") and row.get("email"):
                            email = row["email"]
                            break
        subject = str(profile.get("id") or "")
        display = (profile.get("name") or profile.get("login") or "").strip()
    user = await _upsert_oauth_user(
        db,
        provider="github",
        subject=subject,
        email=email,
        display_name=display,
    )
    return _finish_login(user)


@router.get("/google/start")
async def google_auth_start() -> RedirectResponse:
    if not (settings.google_client_id or "").strip() or not (settings.google_client_secret or "").strip():
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(24)
    _pending_states[state] = "google"
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": _google_auth_redirect(),
            "response_type": "code",
            "scope": GOOGLE_AUTH_SCOPES,
            "access_type": "online",
            "prompt": "select_account",
            "state": state,
        }
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
async def google_auth_callback(
    code: str = "",
    state: str = "",
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if not code or not state or _pending_states.pop(state, None) != "google":
        raise HTTPException(status_code=400, detail="Invalid Google OAuth state")
    async with httpx.AsyncClient(timeout=15) as http:
        token_res = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": _google_auth_redirect(),
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code >= 400:
            raise HTTPException(status_code=400, detail="Google token exchange failed")
        payload = token_res.json()
        access = payload.get("access_token")
        if not access:
            raise HTTPException(status_code=400, detail="Google did not return an access token")
        info_res = await http.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        if info_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not read Google profile")
        info = info_res.json()
        email = (info.get("email") or "").strip()
        subject = str(info.get("sub") or "")
        display = (info.get("name") or "").strip()
    user = await _upsert_oauth_user(
        db,
        provider="google",
        subject=subject,
        email=email,
        display_name=display,
    )
    return _finish_login(user)
