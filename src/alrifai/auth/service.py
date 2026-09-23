"""Database-backed password authentication and session management."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from src.alrifai.authorization.policy import (
    ALL_BUSINESS_CAPABILITIES,
    AuthenticationMethod,
    AssuranceLevel,
    Capability,
    PrincipalType,
    TrustedPrincipal,
    _from_verified_authentication,
)


PASSWORD_HASHER = PasswordHasher()
SESSION_TTL = timedelta(hours=8)


class AuthenticationError(Exception):
    """Expected authentication failure without credential detail."""


@dataclass(frozen=True)
class SessionResult:
    principal: TrustedPrincipal
    session_token: str
    csrf_token: str
    must_change_password: bool


def normalize_username(username: str) -> str:
    value = username.strip().casefold()
    if not value or len(value) > 120 or any(ch.isspace() for ch in value):
        raise ValueError("invalid username")
    return value


def hash_password(password: str, *, minimum_length: int = 12) -> str:
    if len(password) < minimum_length:
        raise ValueError(f"password must contain at least {minimum_length} characters")
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _capabilities_for_roles(role_names: set[str]) -> frozenset[Capability]:
    mapping = {cap.value: cap for cap in Capability}
    return frozenset(mapping[name] for name in role_names if name in mapping)


def _principal_from_row(row: Any, capabilities: frozenset[Capability]) -> TrustedPrincipal:
    return _from_verified_authentication(
        principal_id=row[0],
        principal_type=PrincipalType(row[1].lower()),
        person_id=row[2],
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="frontend-session",
        assurance=AssuranceLevel.HIGH if row[1] == "OWNER" else AssuranceLevel.STANDARD,
        capabilities=ALL_BUSINESS_CAPABILITIES if row[1] == "OWNER" else capabilities,
    )


def _audit(connection, *, entity_id: UUID, action: str, actor_principal_id: UUID | None, after: dict[str, str]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO audit_log (entity_type, entity_id, action, actor_principal_id, after_state, correlation_id)
            VALUES ('AUTHENTICATION', %s, %s, %s, %s::jsonb, %s)
            """,
            (entity_id, action, actor_principal_id, __import__("json").dumps(after), secrets.token_hex(16)),
        )


def create_owner(connection, username: str, password: str) -> UUID:
    username = normalize_username(username)
    if username != "azimpolcu":
        raise ValueError("the approved bootstrap username is azimpolcu")
    password_hash = hash_password(password, minimum_length=8)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SELECT principal_id FROM auth_principals WHERE principal_type='OWNER' FOR UPDATE")
            if cursor.fetchone() is not None:
                raise ValueError("Owner principal already exists")
            cursor.execute(
                """
                INSERT INTO auth_principals (principal_type, status, must_change_password)
                VALUES ('OWNER', 'active', true) RETURNING principal_id
                """
            )
            principal_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO auth_password_credentials (principal_id, username, password_hash) VALUES (%s, %s, %s)",
                (principal_id, username, password_hash),
            )
            _audit(connection, entity_id=principal_id, action="BOOTSTRAP", actor_principal_id=None, after={"event": "owner_bootstrap"})
    return principal_id


def create_pending_account(connection, username: str, password: str) -> UUID:
    username = normalize_username(username)
    password_hash = hash_password(password)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO auth_principals (principal_type, status) VALUES ('APPLICANT','pending') RETURNING principal_id"
            )
            principal_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO auth_password_credentials (principal_id, username, password_hash) VALUES (%s,%s,%s)",
                (principal_id, username, password_hash),
            )
    return principal_id


def authenticate(connection, username: str, password: str) -> SessionResult:
    username = normalize_username(username)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.principal_id, p.principal_type, p.person_id, p.status,
                       p.must_change_password, c.password_hash, c.failed_attempts,
                       c.locked_until
                FROM auth_password_credentials c JOIN auth_principals p USING (principal_id)
                WHERE c.username = %s FOR UPDATE
                """,
                (username,),
            )
            row = cursor.fetchone()
            now = _utcnow()
            if row is None:
                raise AuthenticationError("invalid credentials")
            if row[3] != "active" or (row[7] is not None and row[7] > now):
                raise AuthenticationError("invalid credentials")
            if not verify_password(row[5], password):
                attempts = row[6] + 1
                cursor.execute(
                    "UPDATE auth_password_credentials SET failed_attempts=%s, locked_until=CASE WHEN %s >= 5 THEN %s ELSE locked_until END WHERE principal_id=%s",
                    (attempts, attempts, now + timedelta(minutes=15), row[0]),
                )
                _audit(connection, entity_id=row[0], action="DENY", actor_principal_id=None, after={"event": "login_failed"})
                raise AuthenticationError("invalid credentials")
            cursor.execute(
                "UPDATE auth_password_credentials SET failed_attempts=0, locked_until=NULL, updated_at=NOW() WHERE principal_id=%s",
                (row[0],),
            )
            cursor.execute(
                "SELECT r.role_name FROM auth_principal_roles pr JOIN auth_roles r USING (role_id) WHERE pr.principal_id=%s",
                (row[0],),
            )
            capabilities = _capabilities_for_roles({item[0].lower() for item in cursor.fetchall()})
            token = secrets.token_urlsafe(48)
            csrf = secrets.token_urlsafe(32)
            cursor.execute(
                "INSERT INTO auth_sessions (principal_id, token_hash, csrf_token_hash, expires_at) VALUES (%s,%s,%s,%s)",
                (row[0], _hash_token(token), _hash_token(csrf), now + SESSION_TTL),
            )
            _audit(connection, entity_id=row[0], action="LOGIN", actor_principal_id=row[0], after={"event": "login_success"})
            return SessionResult(_principal_from_row(row, capabilities), token, csrf, row[4])


def load_session(connection, token: str) -> tuple[TrustedPrincipal, str] | None:
    if not token:
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.session_id, s.principal_id, s.csrf_token_hash,
                   p.principal_id, p.principal_type, p.person_id, p.status
            FROM auth_sessions s JOIN auth_principals p USING (principal_id)
            WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at > NOW()
            """,
            (_hash_token(token),),
        )
        row = cursor.fetchone()
        if row is None or row[6] != "active":
            return None
        cursor.execute(
            "SELECT r.role_name FROM auth_principal_roles pr JOIN auth_roles r USING (role_id) WHERE pr.principal_id=%s",
            (row[1],),
        )
        capabilities = _capabilities_for_roles({item[0].lower() for item in cursor.fetchall()})
        cursor.execute("UPDATE auth_sessions SET last_seen_at=NOW() WHERE session_id=%s", (row[0],))
        return _principal_from_row(row[3:], capabilities), row[2]


def revoke_session(connection, token: str, csrf_token: str) -> bool:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_sessions SET revoked_at=NOW() WHERE token_hash=%s AND csrf_token_hash=%s AND revoked_at IS NULL RETURNING principal_id",
                (_hash_token(token), _hash_token(csrf_token)),
            )
            row = cursor.fetchone()
            if row:
                _audit(connection, entity_id=row[0], action="LOGOUT", actor_principal_id=row[0], after={"event": "logout"})
            return row is not None


def change_password(
    connection,
    token: str,
    csrf_token: str,
    new_password: str,
    current_password: str | None = None,
) -> None:
    password_hash = hash_password(new_password)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.session_id, s.principal_id, c.password_hash, p.must_change_password
                FROM auth_sessions s JOIN auth_principals p USING (principal_id)
                JOIN auth_password_credentials c USING (principal_id)
                WHERE s.token_hash=%s AND s.csrf_token_hash=%s AND s.revoked_at IS NULL
                  AND s.expires_at > NOW() AND p.status='active'
                FOR UPDATE
                """,
                (_hash_token(token), _hash_token(csrf_token)),
            )
            row = cursor.fetchone()
            if row is None or (current_password is None and not row[3]):
                raise AuthenticationError("invalid session")
            if current_password is not None and not verify_password(row[2], current_password):
                raise AuthenticationError("current password is incorrect")
            cursor.execute(
                "UPDATE auth_password_credentials SET password_hash=%s, password_changed_at=NOW(), failed_attempts=0, locked_until=NULL, updated_at=NOW() WHERE principal_id=%s",
                (password_hash, row[1]),
            )
            cursor.execute("UPDATE auth_principals SET must_change_password=false, updated_at=NOW() WHERE principal_id=%s", (row[1],))
            cursor.execute("UPDATE auth_sessions SET revoked_at=NOW() WHERE principal_id=%s AND session_id<>%s AND revoked_at IS NULL", (row[1], row[0]))
            _audit(connection, entity_id=row[1], action="UPDATE", actor_principal_id=row[1], after={"event": "password_changed"})


def update_username(connection, token: str, csrf_token: str, username: str) -> None:
    normalized = normalize_username(username)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.principal_id FROM auth_sessions s JOIN auth_principals p USING (principal_id)
                WHERE s.token_hash=%s AND s.csrf_token_hash=%s AND s.revoked_at IS NULL
                  AND s.expires_at > NOW() AND p.status='active' AND p.principal_type='OWNER'
                FOR UPDATE
                """,
                (_hash_token(token), _hash_token(csrf_token)),
            )
            row = cursor.fetchone()
            if row is None:
                raise AuthenticationError("Owner session required")
            cursor.execute(
                "UPDATE auth_password_credentials SET username=%s, updated_at=NOW() WHERE principal_id=%s",
                (normalized, row[0]),
            )
            _audit(connection, entity_id=row[0], action="UPDATE", actor_principal_id=row[0], after={"event": "username_changed"})


def reset_user_password(connection, token: str, csrf_token: str, target_principal_id: UUID, new_password: str) -> None:
    password_hash = hash_password(new_password)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.session_id, s.principal_id FROM auth_sessions s JOIN auth_principals p USING (principal_id)
                WHERE s.token_hash=%s AND s.csrf_token_hash=%s AND s.revoked_at IS NULL
                  AND s.expires_at > NOW() AND s.created_at > NOW() - INTERVAL '15 minutes'
                  AND p.status='active' AND p.principal_type='OWNER'
                FOR UPDATE
                """,
                (_hash_token(token), _hash_token(csrf_token)),
            )
            actor = cursor.fetchone()
            if actor is None:
                raise AuthenticationError("fresh Owner session required")
            cursor.execute("SELECT principal_type FROM auth_principals WHERE principal_id=%s FOR UPDATE", (target_principal_id,))
            target = cursor.fetchone()
            if target is None:
                raise ValueError("account not found")
            if target[0] == "OWNER":
                raise AuthenticationError("use self-service password change for the Owner")
            cursor.execute(
                "UPDATE auth_password_credentials SET password_hash=%s, password_changed_at=NOW(), failed_attempts=0, locked_until=NULL, updated_at=NOW() WHERE principal_id=%s",
                (password_hash, target_principal_id),
            )
            cursor.execute("UPDATE auth_principals SET must_change_password=true, updated_at=NOW() WHERE principal_id=%s", (target_principal_id,))
            cursor.execute("UPDATE auth_sessions SET revoked_at=NOW() WHERE principal_id=%s AND revoked_at IS NULL", (target_principal_id,))
            _audit(connection, entity_id=target_principal_id, action="RESET", actor_principal_id=actor[1], after={"event": "administrative_password_reset"})
