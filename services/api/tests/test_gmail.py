import pytest
from httpx import AsyncClient

from app.guardian.engine import CONNECTOR_NOT_CONNECTED, GuardianContext, guard
from app.models.enums import PermissionDecision
from app.providers.heuristic import heuristic_plan
from app.runtime.capabilities import default_capabilities


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "mail@example.com", "password": "correcthorse", "display_name": "Ayomide"},
    )
    assert response.status_code == 200, response.text


def test_gmail_plan_is_not_chrome():
    plan = heuristic_plan("Open Gmail")
    assert plan.steps[0].tool == "email.read"


def test_gmail_search_plan():
    plan = heuristic_plan("Search my inbox for invoices")
    assert plan.steps[0].tool == "email.search"


def test_gmail_send_plan():
    plan = heuristic_plan("Send an email to ada@example.com")
    assert plan.steps[0].tool == "email.send"
    assert plan.steps[0].input["to"] == "ada@example.com"


def test_send_money_is_not_gmail():
    plan = heuristic_plan("Send money to Ada")
    assert plan.steps[0].tool == "transfer.execute"


def test_gmail_without_connector_is_blocked():
    result = guard(
        GuardianContext(
            tool="email.send",
            action="email.send",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            gmail_connected=False,
        )
    )
    assert result.error_code == CONNECTOR_NOT_CONNECTED
    assert result.unavailable is True


def test_gmail_send_with_connector_asks():
    result = guard(
        GuardianContext(
            tool="email.send",
            action="email.send",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            gmail_connected=True,
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ASK
    assert result.risk.value == "high"


def test_gmail_read_with_connector_allows():
    result = guard(
        GuardianContext(
            tool="email.read",
            action="email.read",
            device_capabilities=default_capabilities("windows"),
            platform="windows",
            gmail_connected=True,
        )
    )
    assert result.unavailable is False
    assert result.decision == PermissionDecision.ALLOW


@pytest.mark.asyncio
async def test_gmail_token_rejected_is_not_connected(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        return None

    monkeypatch.setattr("app.routers.connections.gmail_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/gmail/token", json={"token": "ya29_invalid_token_value"})
    assert response.status_code == 400
    rows = await client.get("/api/v1/connections")
    gmail = next(item for item in rows.json() if item["provider"] == "gmail")
    assert gmail["connected"] is False


@pytest.mark.asyncio
async def test_gmail_token_verified_connects(client: AsyncClient, monkeypatch):
    await _register(client)

    async def fake_whoami(token: str, client=None):
        assert token == "ya29_valid_example"
        return {"email": "ayomide@gmail.com"}

    monkeypatch.setattr("app.routers.connections.gmail_whoami", fake_whoami)
    response = await client.post("/api/v1/connections/gmail/token", json={"token": "ya29_valid_example"})
    assert response.status_code == 200
    assert response.json()["email"] == "ayomide@gmail.com"
    rows = await client.get("/api/v1/connections")
    payload = rows.json()
    gmail = next(item for item in payload if item["provider"] == "gmail")
    assert gmail["connected"] is True
    assert gmail["account"] == "ayomide@gmail.com"
    calendar = next(item for item in payload if item["provider"] == "google_calendar")
    contacts = next(item for item in payload if item["provider"] == "google_contacts")
    assert calendar["connected"] is False
    assert contacts["connected"] is False


@pytest.mark.asyncio
async def test_gmail_oauth_start_without_client_id(client: AsyncClient):
    await _register(client)
    response = await client.get("/api/v1/connections/gmail/oauth/start", follow_redirects=False)
    assert response.status_code == 400
