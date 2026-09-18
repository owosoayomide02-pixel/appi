import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "voice@example.com", "password": "correcthorse", "display_name": "Ayomide"},
    )
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_voice_prefs_saved_when_device_offline(client: AsyncClient):
    await _register(client)
    start = await client.post("/api/v1/devices/pair/start")
    code = start.json()["pairing_code"]
    complete = await client.post(
        "/api/v1/devices/pair/complete",
        json={"pairing_code": code, "name": "AYOMIDE-LAPTOP", "os": "Windows 11"},
    )
    device_id = complete.json()["device_id"]
    token = complete.json()["device_token"]
    response = await client.patch(
        f"/api/v1/devices/{device_id}/voice",
        json={"tts_voice": "Microsoft Zira Desktop", "culture": "en-GB"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["applied"] is False
    assert body["voice"]["tts_voice"] == "Microsoft Zira Desktop"
    listed = await client.get("/api/v1/devices")
    device = next(item for item in listed.json() if item["id"] == device_id)
    assert device["voice"]["tts_voice"] == "Microsoft Zira Desktop"
    pulled = await client.get("/api/v1/runtime/voice-prefs", params={"token": token})
    assert pulled.status_code == 200
    assert pulled.json()["culture"] == "en-GB"
