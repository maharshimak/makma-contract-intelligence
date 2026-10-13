import hashlib
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import (
    AuthIdentity,
    PasswordCredential,
    User,
    UserSession,
)

password_hash = PasswordHash.recommended()
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: str) -> str:
    email = value.strip().casefold()
    if len(email) > 320 or not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("invalid_email")
    return email


def validate_password(value: str) -> None:
    if len(value) < 12 or len(value) > 128:
        raise ValueError("weak_password")
    if not any(character.isalpha() for character in value) or not any(
        character.isdigit() for character in value
    ):
        raise ValueError("weak_password")


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_password_identity(db: Session, user: User, raw_password: str) -> AuthIdentity:
    validate_password(raw_password)
    identity = AuthIdentity(user_id=user.id, provider="password", provider_subject=user.email)
    db.add(identity)
    db.flush()
    db.add(
        PasswordCredential(
            auth_identity_id=identity.id,
            password_hash=password_hash.hash(raw_password),
        )
    )
    return identity


def verify_password_identity(db: Session, email: str, raw_password: str) -> User | None:
    try:
        normalized = normalize_email(email)
    except ValueError:
        return None
    row = db.execute(
        select(User, PasswordCredential)
        .join(AuthIdentity, AuthIdentity.user_id == User.id)
        .join(PasswordCredential, PasswordCredential.auth_identity_id == AuthIdentity.id)
        .where(
            AuthIdentity.provider == "password",
            AuthIdentity.provider_subject == normalized,
            User.status == "ACTIVE",
        )
    ).first()
    if row is None:
        return None
    valid, updated_hash = password_hash.verify_and_update(raw_password, row[1].password_hash)
    if not valid:
        return None
    if updated_hash:
        row[1].password_hash = updated_hash
    return row[0]


@dataclass(frozen=True)
class NewSession:
    record: UserSession
    token: str
    csrf_token: str


def create_session(db: Session, user: User, settings: Settings) -> NewSession:
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    record = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.session_lifetime_hours),
    )
    db.add(record)
    db.flush()
    return NewSession(record, token, csrf_token)


class AuthRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, settings: Settings) -> bool:
        now = time.monotonic()
        cutoff = now - settings.auth_rate_limit_window_seconds
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] < cutoff:
                attempts.popleft()
            if len(attempts) >= settings.auth_rate_limit_attempts:
                return False
            attempts.append(now)
            return True


auth_rate_limiter = AuthRateLimiter()
