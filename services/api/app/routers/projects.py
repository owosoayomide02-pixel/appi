from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.tables import AllowedFolder, Project, ProjectFile, User, new_id
from app.permissions.path_guard import PathNotAllowed, validate_allowed_folder

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    root_path: str
    device_id: str | None = None


class IndexIn(BaseModel):
    files: list[dict[str, Any]] = Field(default_factory=list)
    framework: str | None = None
    language: str | None = None


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    rows = (await db.execute(select(Project).where(Project.user_id == user.id))).scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "root_path": p.root_path,
            "framework": p.framework,
            "language": p.language,
            "last_indexed_at": p.last_indexed_at.isoformat() if p.last_indexed_at else None,
        }
        for p in rows
    ]


@router.post("")
async def create_project(payload: ProjectIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    try:
        path = validate_allowed_folder(payload.root_path)
    except PathNotAllowed as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    folders = (await db.execute(select(AllowedFolder).where(AllowedFolder.user_id == user.id))).scalars().all()
    if folders:
        from app.permissions.path_guard import validate_path

        try:
            validate_path(path, [f.path for f in folders])
        except PathNotAllowed as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    project = Project(id=new_id(), user_id=user.id, name=payload.name, root_path=path)
    db.add(project)
    await db.commit()
    return {"id": project.id, "name": project.name, "root_path": project.root_path}


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    files = (await db.execute(select(ProjectFile).where(ProjectFile.project_id == project.id))).scalars().all()
    return {
        "id": project.id,
        "name": project.name,
        "root_path": project.root_path,
        "framework": project.framework,
        "language": project.language,
        "files": [{"path": f.path, "language": f.language, "summary": f.summary} for f in files[:400]],
    }


@router.post("/{project_id}/index")
async def index_project(
    project_id: str,
    payload: IndexIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    from datetime import UTC, datetime

    project = await db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    existing = (await db.execute(select(ProjectFile).where(ProjectFile.project_id == project.id))).scalars().all()
    for row in existing:
        await db.delete(row)
    for item in payload.files[:2000]:
        db.add(
            ProjectFile(
                id=new_id(),
                project_id=project.id,
                path=str(item.get("path", "")),
                language=item.get("language"),
                content_hash=item.get("hash"),
                summary=item.get("summary"),
            )
        )
    project.framework = payload.framework
    project.language = payload.language
    project.last_indexed_at = datetime.now(UTC)
    await db.commit()
    return {"indexed": min(len(payload.files), 2000)}
