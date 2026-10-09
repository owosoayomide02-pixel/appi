"""
LiveKit voice-agent token endpoint.
Returns a short-lived LiveKit access token so the browser can join the
voice room, and dispatches the APPI agent into that room.
Only authenticated APPI users can call this endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from livekit.api import AccessToken, VideoGrants, LiveKitAPI, CreateAgentDispatchRequest

from app.config import settings
from app.deps import get_current_user
from app.models.tables import User

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.get("/token")
async def get_voice_token(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Generate a LiveKit access token for the logged-in user and dispatch
    the APPI voice agent into their private room.
    The frontend calls this, then passes the token to <LiveKitRoom>.
    """
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(
            status_code=503,
            detail="Voice agent is not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in .env",
        )

    # Each user gets their own private room
    room_name = f"appi-voice-{current_user.id}"
    participant_name = current_user.display_name or str(current_user.id)

    # 1. Mint the access token for the browser
    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(str(current_user.id))
        .with_name(participant_name)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    # 2. Dispatch the agent into the room so it actually shows up and talks
    # This tells LiveKit Cloud: "send the 'my-agent' worker into this room"
    try:
        async with LiveKitAPI(
            url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ) as lk:
            await lk.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    agent_name="my-agent",  # must match @server.rtc_session(agent_name=) in agent.py
                    room=room_name,
                )
            )
    except Exception as exc:
        # If dispatch fails (e.g. agent not running yet), still return the token
        # so the frontend can connect — the agent just won't be in the room yet
        print(f"[voice] Agent dispatch failed (is the agent running?): {exc}")

    return {
        "token": token,
        "room": room_name,
        "livekit_url": settings.livekit_url,
        "identity": str(current_user.id),
    }
