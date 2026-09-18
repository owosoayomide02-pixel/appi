import pytest
from httpx import AsyncClient

from app.guardian.engine import CONNECTOR_NOT_CONNECTED, GuardianContext, guard
from app.models.enums import PermissionDecision
from app.providers.heuristic import heuristic_plan
from app.runtime.capabilities import default_capabilities


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "cal@example.com", "password": "correcthorse", "display_name": "Ayomide"},
    )
    assert response.status_code == 200, response.text


def test_calendar_plan_is_not_chrome():
    plan = heuristic_plan("What's on my Google Calendar")
    assert plan.steps[0].tool == "calendar.read"


def test_calendar_schedule_plan():
    plan = heuristic_plan("Schedule a meeting with Ada")
    assert plan.steps[0].tool == "calendar.write"


def test_calendar_without_connector_is_blocked():
    result = guard(
        GuardianContext(
            tool="calendar.write",
            action="calendar.write",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            calendar_connected=False,
        )
    )
    assert result.error_code == CONNECTOR_NOT_CONNECTED
    assert result.unavailable is True


def test_calendar_write_with_connector_asks():
    result = guard(
        GuardianContext(
            tool="calendar.write",
            action="calendar.write",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            calendar_connected=True,
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ASK


def test_calendar_read_with_connector_allows():
    result = guard(
        GuardianContext(
            tool="calendar.read",
            action="calendar.read",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            calendar_connected=True,
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ALLOW


@pytest.mark.asyncio
async def test_calendar_token_rejected_is_not_connected(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        return None

    monkeypatch.setattr("app.routers.connections.calendar_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/google_calendar/token", json={"token": "ya29_invalid_token_value"})
    assert response.status_code == 400
    rows = await client.get("/api/v1/connections")
    calendar = next(item for item in rows.json() if item["provider"] == "google_calendar")
    assert calendar["connected"] is False


@pytest.mark.asyncio
async def test_calendar_token_verified_connects(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        assert token == "ya29_valid_calendar"
        return {"email": "ayomide@gmail.com", "calendar_id": "primary"}

    monkeypatch.setattr("app.routers.connections.calendar_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/google_calendar/token", json={"token": "ya29_valid_calendar"})
    assert response.status_code == 200
    assert response.json()["email"] == "ayomide@gmail.com"
    rows = await client.get("/api/v1/connections")
    payload = rows.json()
    calendar = next(item for item in payload if item["provider"] == "google_calendar")
    assert calendar["connected"] is True
    assert calendar["account"] == "ayomide@gmail.com"
    gmail = next(item for item in payload if item["provider"] == "gmail")
    contacts = next(item for item in payload if item["provider"] == "google_contacts")
    assert gmail["connected"] is False
    assert contacts["connected"] is False


@pytest.mark.asyncio
async def test_calendar_oauth_start_without_client_id(client: AsyncClient):
    await _register(client)
    response = await client.get("/api/v1/connections/google_calendar/oauth/start", follow_redirects=False)
    assert response.status_code == 400
