"""Canonical AI gateway configuration types and validation.

A gateway is an approved model-serving endpoint (9Router combo routing,
another OpenAI-compatible endpoint, Ollama/local model). 9Router keeps
owning its internal provider fallback; AL-RIFAI only owns which approved
gateway/route is active plus an optional application-level fallback gateway.

Secrets are never stored here: ``secret_ref`` names a server-side secret
(``env:NAME`` or ``file:/path``) resolved only by ``SecretResolver``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit


class AiConfigError(ValueError):
    """A gateway configuration is invalid and cannot become active."""


class GatewayType(StrEnum):
    NINE_ROUTER = "nine_router"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LOCAL_MODEL = "local_model"


class GatewayAuthMode(StrEnum):
    API_KEY = "api_key"
    NONE = "none"


MAX_ID_CHARS = 64
MAX_TEXT_CHARS = 256
MAX_ROUTE_CHARS = 128


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    """One approved AI gateway. ``secret_ref`` is a reference, never a secret."""

    gateway_id: str
    display_name: str
    gateway_type: GatewayType
    endpoint: str
    auth_mode: GatewayAuthMode
    secret_ref: str | None
    route: str
    enabled: bool
    is_local: bool
    fallback_gateway_id: str | None = None
    config_version: int = 1
    updated_by: str | None = None
    updated_at: datetime | None = None
    last_test_at: datetime | None = None
    last_test_ok: bool | None = None


@dataclass(frozen=True, slots=True)
class GatewayView:
    """Safe, browser-visible projection. No credential values."""

    gateway_id: str
    display_name: str
    gateway_type: GatewayType
    endpoint: str
    auth_mode: GatewayAuthMode
    route: str
    enabled: bool
    is_local: bool
    fallback_gateway_id: str | None
    config_version: int
    credential_configured: bool
    last_test_at: datetime | None
    last_test_ok: bool | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class AiRuntimeView:
    gateways: tuple[GatewayView, ...] = field(default_factory=tuple)
    active_gateway_id: str | None = None
    persistence_available: bool = True
    persistence_note: str | None = None


def validate_gateway(config: GatewayConfig, known_ids: set[str] | frozenset[str]) -> None:
    """Raise AiConfigError when the config must not become active."""
    if not config.gateway_id.strip() or len(config.gateway_id) > MAX_ID_CHARS:
        raise AiConfigError("gateway_id must be non-empty bounded text")
    if any(ch.isspace() for ch in config.gateway_id):
        raise AiConfigError("gateway_id must not contain whitespace")
    if not config.display_name.strip() or len(config.display_name) > MAX_TEXT_CHARS:
        raise AiConfigError("display_name must be non-empty bounded text")
    if not isinstance(config.gateway_type, GatewayType):
        raise AiConfigError("unsupported gateway type")
    if not isinstance(config.auth_mode, GatewayAuthMode):
        raise AiConfigError("unsupported auth mode")
    _validate_endpoint(config.endpoint)
    if not config.route.strip() or len(config.route) > MAX_ROUTE_CHARS:
        raise AiConfigError("route must be non-empty bounded text")
    if config.auth_mode is GatewayAuthMode.API_KEY:
        if config.secret_ref is None or not config.secret_ref.strip():
            raise AiConfigError("api_key gateways require a secret_ref")
        _validate_secret_ref(config.secret_ref)
    else:
        if config.secret_ref is not None:
            raise AiConfigError("auth-mode none must not carry a secret_ref")
    if config.fallback_gateway_id is not None:
        if config.fallback_gateway_id == config.gateway_id:
            raise AiConfigError("a gateway cannot fall back to itself")
        if config.fallback_gateway_id not in known_ids:
            raise AiConfigError("fallback gateway is unknown")
    if config.config_version < 1:
        raise AiConfigError("config_version must be positive")


def _validate_endpoint(endpoint: str) -> None:
    if not endpoint.strip() or len(endpoint) > MAX_TEXT_CHARS:
        raise AiConfigError("endpoint must be non-empty bounded text")
    try:
        parsed = urlsplit(endpoint.strip())
    except ValueError as exc:
        raise AiConfigError("endpoint is not a valid URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AiConfigError("endpoint must be an http(s) URL with a host")
    if parsed.username or parsed.password:
        raise AiConfigError("endpoint must not embed credentials")


def _validate_secret_ref(secret_ref: str) -> None:
    if secret_ref.startswith("env:"):
        name = secret_ref[4:]
        if not name.strip() or any(ch.isspace() for ch in name):
            raise AiConfigError("env secret_ref must name one variable")
    elif secret_ref.startswith("file:"):
        path = secret_ref[5:]
        if not path.strip() or len(path) > MAX_TEXT_CHARS:
            raise AiConfigError("file secret_ref must be a bounded path")
    else:
        raise AiConfigError("secret_ref must use env:NAME or file:/path")
