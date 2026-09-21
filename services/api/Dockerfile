# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

COPY services/api/pyproject.toml ./
COPY services/api/app ./app

RUN pip install --upgrade pip \
  && pip install \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "sqlalchemy[asyncio]>=2.0.36" \
    "aiosqlite>=0.20.0" \
    "asyncpg>=0.30.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0" \
    "PyJWT>=2.10.0" \
    "bcrypt>=4.2.0" \
    "cryptography>=44.0.0" \
    "httpx>=0.28.0" \
    "websockets>=14.0" \
    "jsonschema>=4.23.0" \
    "python-multipart>=0.0.18" \
    "email-validator>=2.2.0"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
