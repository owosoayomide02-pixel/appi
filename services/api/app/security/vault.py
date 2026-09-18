import base64
import hashlib
import os
import re
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

HANDLE_RE = re.compile(r"^secret://[a-z0-9_\-./]+$", re.IGNORECASE)


def _derive_fernet_key(raw: str) -> bytes:
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = settings.encryption_key or settings.jwt_secret
    return Fernet(_derive_fernet_key(key))


def make_handle(provider: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9_\-]+", "-", f"{provider}/{name}".lower())
    return f"secret://{slug}"


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt secret") from exc


def is_handle(value: str) -> bool:
    return bool(HANDLE_RE.match(value.strip()))


def random_token(nbytes: int = 32) -> str:
    return base64.urlsafe_b64encode(os.urandom(nbytes)).decode("utf-8").rstrip("=")
