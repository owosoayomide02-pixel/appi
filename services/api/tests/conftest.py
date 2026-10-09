import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["AI_PROVIDER"] = "heuristic"
os.environ["AI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_ANON_KEY"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["NEXT_PUBLIC_SUPABASE_URL"] = ""
os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = ""
os.environ["GITHUB_CLIENT_ID"] = ""
os.environ["GITHUB_CLIENT_SECRET"] = ""
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import Base, engine, init_db
from app.main import create_app
from app.security.kill_switch import kill_switch


@pytest_asyncio.fixture
async def client():
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    kill_switch._users.clear()
