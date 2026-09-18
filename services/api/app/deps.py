from fastapi import Cookie, Depends, HTTPException, Request, status
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import User
from app.security.rate_limit import limiter
from app.security.tokens import decode_access_token


async def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    auth = request.cookies.get("access_token") or request.headers.get("authorization", "")
    if auth:
        key = f"auth:{auth[-24:]}"
    if not limiter.allow(key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    token = access_token
    if not token:
        header = request.headers.get("authorization") or ""
        if header.lower().startswith("bearer "):
            token = header.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
