from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.integrations.catalog import CONNECTORS
from app.models.tables import Connection, User, UserPolicy, new_id
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_OPTS = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,
    "max_age": 60 * 60 * 24 * 7,
    "path": "/",
}


class AuthPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    onboarding_completed: bool
    kill_switch_active: bool
    theme: str
    access_token: str | None = None


def serialize_user(user: User, token: str | None = None) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "onboarding_completed": user.onboarding_completed,
        "kill_switch_active": user.kill_switch_active,
        "theme": user.theme,
        "access_token": token,
    }


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


@router.post("/register", response_model=UserOut)
async def register(payload: AuthPayload, response: Response, db: AsyncSession = Depends(get_db)) -> Any:
    existing = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        id=new_id(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.email.split("@")[0],
    )
    db.add(user)
    db.add(UserPolicy(id=new_id(), user_id=user.id))
    for conn in _seed_connections(user.id):
        db.add(conn)
    await db.commit()
    token = create_access_token(user.id)
    response.set_cookie("access_token", token, **COOKIE_OPTS)
    return serialize_user(user, token)


@router.post("/login", response_model=UserOut)
async def login(payload: AuthPayload, response: Response, db: AsyncSession = Depends(get_db)) -> Any:
    user = (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    response.set_cookie("access_token", token, **COOKIE_OPTS)
    return serialize_user(user, token)


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("access_token", path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> Any:
    return serialize_user(user)


@router.get("/ws-token")
async def ws_token(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"token": create_access_token(user.id, extra={"typ": "ws"})}
