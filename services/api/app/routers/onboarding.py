from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tables import AllowedFolder, User, UserPolicy, new_id
from app.permissions.path_guard import PathNotAllowed, validate_allowed_folder
from app.realtime.hub import hub

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


class FolderIn(BaseModel):
    path: str
    device_id: str | None = None


class OnboardingFinish(BaseModel):
    theme: str | None = "dark"


@router.get("/folders")
async def list_folders(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = (await db.execute(select(AllowedFolder).where(AllowedFolder.user_id == user.id))).scalars().all()
    return [{"id": r.id, "path": r.path} for r in rows]


@router.post("/folders")
async def add_folder(payload: FolderIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    try:
        path = validate_allowed_folder(payload.path)
    except PathNotAllowed as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = AllowedFolder(id=new_id(), user_id=user.id, device_id=payload.device_id, path=path)
    db.add(row)
    await db.commit()
    return {"id": row.id, "path": path}


@router.delete("/folders/{folder_id}")
async def remove_folder(folder_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, str]:
    row = await db.get(AllowedFolder, folder_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Folder not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted"}


@router.post("/complete")
async def complete(payload: OnboardingFinish, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    user.onboarding_completed = True
    if payload.theme in {"dark", "light"}:
        user.theme = payload.theme
    policy = (await db.execute(select(UserPolicy).where(UserPolicy.user_id == user.id))).scalar_one_or_none()
    folders = (await db.execute(select(AllowedFolder).where(AllowedFolder.user_id == user.id))).scalars().all()
    await db.commit()
    return {
        "onboarding_completed": True,
        "folders": len(folders),
        "policy_ready": policy is not None,
    }


@router.get("/connection-test")
async def connection_test(user: User = Depends(get_current_user)) -> dict[str, Any]:
    from sqlalchemy import select as sel
    from app.models.tables import Device

    # Lightweight liveness for setup step 6.
    return {
        "api": True,
        "kill_switch": user.kill_switch_active,
        "device_online": any(hub.device_online(d) for d in hub.devices),
    }
