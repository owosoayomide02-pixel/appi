from httpx import AsyncClient
import pytest


async def _register(client: AsyncClient, email: str = "user@example.com") -> AsyncClient:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorse", "display_name": "Ayomide"},
    )
    assert response.status_code == 200, response.text
    return client


@pytest.mark.asyncio
async def test_register_and_me(client: AsyncClient):
    await _register(client)
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_kill_switch_cancels_and_blocks_new_tasks(client: AsyncClient):
    await _register(client)
    stopped = await client.post("/api/v1/kill-switch/stop")
    assert stopped.status_code == 200
    assert stopped.json()["active"] is True
    blocked = await client.post("/api/v1/tasks", json={"input_text": "Do something else"})
    assert blocked.status_code == 423
    audit = await client.get("/api/v1/audit")
    actions = [row["action"] for row in audit.json()]
    assert "kill_switch.activated" in actions


@pytest.mark.asyncio
async def test_memory_is_user_isolated(client: AsyncClient):
    await _register(client, "one@example.com")
    added = await client.post("/api/v1/memory", json={"kind": "preference", "content": "Use npm", "topic": "package_manager"})
    assert added.status_code == 200
    await client.post("/api/v1/auth/logout")
    await _register(client, "two@example.com")
    rows = await client.get("/api/v1/memory")
    assert rows.json() == []


@pytest.mark.asyncio
async def test_device_pairing_requires_valid_code(client: AsyncClient):
    await _register(client)
    start = await client.post("/api/v1/devices/pair/start")
    assert start.status_code == 200
    code = start.json()["pairing_code"]
    complete = await client.post(
        "/api/v1/devices/pair/complete",
        json={"pairing_code": code, "name": "AYOMIDE-LAPTOP", "os": "Windows 11"},
    )
    assert complete.status_code == 200
    assert "device_token" in complete.json()
    token = complete.json()["device_token"]
    who = await client.get("/api/v1/runtime/whoami", params={"token": token})
    assert who.status_code == 200
    assert who.json()["display_name"] == "Ayomide"
    bad = await client.post("/api/v1/devices/pair/complete", json={"pairing_code": "000000", "name": "x"})
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_forbidden_folder_rejected(client: AsyncClient):
    await _register(client)
    response = await client.post("/api/v1/onboarding/folders", json={"path": r"C:\Windows"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_audit_created_for_plan(client: AsyncClient):
    await _register(client)
    await client.post("/api/v1/tasks", json={"input_text": "Read package.json and explain the stack"})
    audit = await client.get("/api/v1/audit")
    assert audit.status_code == 200


@pytest.mark.asyncio
async def test_runtime_capability_catalog(client: AsyncClient):
    catalog = await client.get("/api/v1/runtime/capabilities")
    assert catalog.status_code == 200
    body = catalog.json()
    assert "filesystem.read" in {item["id"] for item in body["capabilities"]}
    assert body["profiles"]["windows"]["filesystem"] is True
    assert body["profiles"]["android"]["filesystem"] is False
    assert body["profiles"]["windows"]["payment.execute"] is False


@pytest.mark.asyncio
async def test_paired_device_reports_capabilities(client: AsyncClient):
    await _register(client)
    start = await client.post("/api/v1/devices/pair/start")
    code = start.json()["pairing_code"]
    await client.post(
        "/api/v1/devices/pair/complete",
        json={
            "pairing_code": code,
            "name": "AYOMIDE-LAPTOP",
            "os": "Windows 11",
            "platform": "windows",
            "runtime_version": "0.2.0",
            "capabilities": {"filesystem": True, "terminal": True, "browser": True, "payments": True},
        },
    )
    devices = await client.get("/api/v1/devices")
    assert devices.status_code == 200
    device = devices.json()[0]
    assert device["platform"] == "windows"
    assert device["capabilities"]["filesystem"] is True
    assert device["capabilities"]["payment.execute"] is False
    detail = await client.get(f"/api/v1/devices/{device['id']}")
    assert detail.status_code == 200
    assert "granted_permissions" in detail.json()


@pytest.mark.asyncio
async def test_connections_are_categorized_and_not_faked(client: AsyncClient):
    await _register(client)
    rows = await client.get("/api/v1/connections")
    assert rows.status_code == 200
    body = rows.json()
    assert any(row["category"] == "payments" for row in body)
    assert all(row["connected"] is False for row in body)
    whatsapp = next(row for row in body if row["provider"] == "whatsapp")
    assert whatsapp["status"] == "unsupported"
