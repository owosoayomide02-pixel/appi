from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/v1/downloads", tags=["downloads"])

_INSTALLERS = Path(__file__).resolve().parent.parent / "installers"
_WINDOWS_CACHE = Path("/tmp/Appi-windows.zip")


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


def _api_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _windows_public_url() -> str:
    """Prefer an explicitly public URL; otherwise visitors use the API proxy."""
    return (settings.download_windows_url or "").strip()


@router.get("")
async def download_manifest(request: Request) -> dict:
    """Public installer manifest — OS auto-detect from User-Agent."""
    detected = _detect(request.headers.get("user-agent", ""))
    base = _api_base(request)
    # Always point the UI at API file endpoints so private GitHub repos still work.
    win_url = f"{base}/api/v1/downloads/windows"
    mac_url = f"{base}/api/v1/downloads/macos"
    linux_url = f"{base}/api/v1/downloads/linux"
    platforms = [
        PlatformAsset(
            id="windows",
            label="Windows",
            kind="exe",
            url=win_url,
            filename="Appi-windows.zip",
            available=True,
            blurb="Download the Appi desktop app (zip). Unzip, open Appi.exe, then pair with a Devices code.",
            pair_template="Appi.exe pair --code {code}",
        ),
        PlatformAsset(
            id="macos",
            label="macOS",
            kind="macos",
            url=mac_url,
            filename="setup-macos.sh",
            available=(_INSTALLERS / "setup-macos.sh").is_file(),
            blurb="Run the macOS setup script — installs Appi, connects to the live site, then pair.",
            pair_template="python3 -m app.main pair --code {code}",
        ),
        PlatformAsset(
            id="linux",
            label="Linux",
            kind="linux",
            url=linux_url,
            filename="setup-linux.sh",
            available=(_INSTALLERS / "setup-linux.sh").is_file(),
            blurb="Run the Linux setup script — installs Appi, connects to the live site, then pair.",
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


async def _ensure_windows_zip() -> Path:
    """Cache the Windows zip locally (from public URL or GitHub API with token)."""
    if _WINDOWS_CACHE.is_file() and _WINDOWS_CACHE.stat().st_size > 1_000_000:
        return _WINDOWS_CACHE

    public = _windows_public_url()
    token = (settings.github_token or "").strip()
    repo = settings.github_repo or "owosoayomide02-pixel/appi"
    tag = settings.download_windows_tag or "v0.3.0"

    headers = {"User-Agent": "appi-downloads", "Accept": "application/octet-stream"}
    url = public

    if token:
        # Private-repo safe: resolve the release asset via the GitHub API.
        headers["Authorization"] = f"Bearer {token}"
        api = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            meta = await client.get(api, headers={**headers, "Accept": "application/vnd.github+json"})
            if meta.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Could not read GitHub release {tag}")
            assets = meta.json().get("assets") or []
            match = next((a for a in assets if a.get("name") == "Appi-windows.zip"), None)
            if not match:
                raise HTTPException(status_code=404, detail="Appi-windows.zip missing from release")
            url = match["url"]
            asset = await client.get(url, headers=headers)
            if asset.status_code != 200:
                raise HTTPException(status_code=502, detail="Could not download Windows installer asset")
            _WINDOWS_CACHE.parent.mkdir(parents=True, exist_ok=True)
            _WINDOWS_CACHE.write_bytes(asset.content)
            return _WINDOWS_CACHE

    if not url:
        raise HTTPException(
            status_code=503,
            detail="Windows installer unavailable. Set GITHUB_TOKEN on the API or DOWNLOAD_WINDOWS_URL to a public zip.",
        )

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        asset = await client.get(url, headers=headers)
        if asset.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not fetch Windows installer")
        _WINDOWS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _WINDOWS_CACHE.write_bytes(asset.content)
        return _WINDOWS_CACHE


@router.get("/windows")
async def download_windows():
    """Serve the Windows zip (proxied/cached so private GitHub repos still work)."""
    public = _windows_public_url()
    # If the URL is already a public HTTP(S) file (not github private), redirect.
    if public and "github.com" not in public and "githubusercontent.com" not in public:
        return RedirectResponse(url=public, status_code=302)
    if public and not (settings.github_token or "").strip():
        # Try public redirect first (works when the repo is public).
        return RedirectResponse(url=public, status_code=302)

    path = await _ensure_windows_zip()
    return FileResponse(
        path,
        media_type="application/zip",
        filename="Appi-windows.zip",
        headers={"Content-Disposition": 'attachment; filename="Appi-windows.zip"'},
    )


@router.get("/macos")
async def download_macos():
    path = _INSTALLERS / "setup-macos.sh"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="macOS setup script missing")
    return FileResponse(
        path,
        media_type="application/x-sh",
        filename="setup-macos.sh",
        headers={"Content-Disposition": 'attachment; filename="setup-macos.sh"'},
    )


@router.get("/linux")
async def download_linux():
    path = _INSTALLERS / "setup-linux.sh"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Linux setup script missing")
    return FileResponse(
        path,
        media_type="application/x-sh",
        filename="setup-linux.sh",
        headers={"Content-Disposition": 'attachment; filename="setup-linux.sh"'},
    )
