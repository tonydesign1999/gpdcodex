import hashlib
import secrets
from datetime import datetime, timedelta

from app.core.config import settings


class TokenStore:
    """简单内存 Token 存储，用于局域网第一版。"""

    def __init__(self) -> None:
        self._tokens: dict[str, tuple[str, datetime]] = {}

    def create_token(self, username: str) -> str:
        token = secrets.token_hex(24)
        expire_at = datetime.utcnow() + timedelta(minutes=settings.token_expire_minutes)
        self._tokens[token] = (username, expire_at)
        return token

    def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

    def verify(self, token: str) -> str | None:
        token_info = self._tokens.get(token)
        if not token_info:
            return None
        username, expire_at = token_info
        if expire_at < datetime.utcnow():
            self._tokens.pop(token, None)
            return None
        return username


token_store = TokenStore()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
