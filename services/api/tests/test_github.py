import pytest
from httpx import AsyncClient

from app.guardian.engine import CONNECTOR_NOT_CONNECTED, GuardianContext, guard
from app.providers.heuristic import heuristic_plan
from app.runtime.capabilities import default_capabilities


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "git@example.com", "password": "correcthorse", "display_name": "Ayomide"},
    )
    assert response.status_code == 200, response.text


def test_github_plan():
    plan = heuristic_plan("List my GitHub repos")
    assert plan.steps[0].tool == "github.repos"


def test_github_without_connector_is_blocked():
    result = guard(
        GuardianContext(
            tool="github.repos",
            action="github.repos",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            github_connected=False,
        )
    )
    assert result.error_code == CONNECTOR_NOT_CONNECTED


def test_github_with_connector_allows_read():
    result = guard(
        GuardianContext(
            tool="github.user",
            action="github.user",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            github_connected=True,
        )
    )
    assert result.unavailable is False
    assert result.decision.value == "ALLOW"


@pytest.mark.asyncio
async def test_github_pat_rejected_is_not_connected(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        return None

    monkeypatch.setattr("app.routers.connections.github_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/github/token", json={"token": "ghp_invalid_token_value"})
    assert response.status_code == 400
    rows = await client.get("/api/v1/connections")
    github = next(item for item in rows.json() if item["provider"] == "github")
    assert github["connected"] is False


@pytest.mark.asyncio
async def test_github_pat_verified_connects(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        assert token == "ghp_valid_example"
        return {"login": "ayomide", "id": 42}

    monkeypatch.setattr("app.routers.connections.github_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/github/token", json={"token": "ghp_valid_example"})
    assert response.status_code == 200
    assert response.json()["login"] == "ayomide"
    rows = await client.get("/api/v1/connections")
    github = next(item for item in rows.json() if item["provider"] == "github")
    assert github["connected"] is True
    assert github["account"] == "ayomide"


@pytest.mark.asyncio
async def test_github_oauth_device_without_client_id(client: AsyncClient):
    await _register(client)
    response = await client.post("/api/v1/connections/github/oauth/device")
    assert response.status_code == 400
