from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/v1/downloads", tags=["downloads"])


class PlatformAsset(BaseModel):
    id: str
    label: str
    kind: str
    url: str
    filename: str
    available: bool
    blurb: str
    pair_template: str


def _detect(ua: str) -> str:
    raw = (ua or "").lower()
    if "win" in raw:
        return "windows"
    if "mac" in raw or "iphone" in raw or "ipad" in raw:
        return "macos"
    if "linux" in raw or "android" in raw or "cros" in raw:
        return "linux"
    return "unknown"


@router.get("")
async def download_manifest(request: Request) -> dict:
    """Public installer manifest — OS auto-detect from User-Agent + env URLs."""
    detected = _detect(request.headers.get("user-agent", ""))
    platforms = [
        PlatformAsset(
            id="windows",
            label="Windows",
            kind="exe",
            url=settings.download_windows_url,
            filename="Appi-windows.zip",
            available=bool(settings.download_windows_url),
            blurb="Download Appi.exe (zip). Unzip, then pair with your account.",
            pair_template="Appi.exe pair --code {code}",
        ),
        PlatformAsset(
            id="macos",
            label="macOS",
            kind="macos",
            url=settings.download_macos_url,
            filename="setup-macos.sh",
            available=bool(settings.download_macos_url),
            blurb="Run the macOS setup script on a Mac (LaunchAgent).",
            pair_template="python3 -m app.main pair --code {code}",
        ),
        PlatformAsset(
            id="linux",
            label="Linux",
            kind="linux",
            url=settings.download_linux_url,
            filename="setup-linux.sh",
            available=bool(settings.download_linux_url),
            blurb="Run the Linux setup script (systemd user service).",
            pair_template="python3 -m app.main pair --code {code}",
        ),
    ]
    recommended = next((p for p in platforms if p.id == detected), platforms[0])
    return {
        "detected": detected,
        "recommended": recommended.model_dump(),
        "platforms": [p.model_dump() for p in platforms],
        "app_url": settings.public_app_url,
        "api_url": settings.public_api_url,
        "runtime_version": settings.runtime_version,
        "github_repo": settings.github_repo,
    }
