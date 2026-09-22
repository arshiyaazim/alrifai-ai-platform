"""Canonical AI runtime service.

All reads serve the safe view (no credential values). All mutations require
the trusted ``MANAGE_CONFIGURATION`` capability. Connection testing and model
discovery run backend-side so browsers never touch gateway credentials.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from uuid import UUID

from ..authorization.policy import Capability, require_capability
from .config import (
    AiConfigError,
    AiRuntimeView,
    GatewayConfig,
    GatewayView,
    validate_gateway,
)
from .secrets import SecretMissing, SecretResolver
from .stores import InMemoryAiRuntimeStore, PostgresAiRuntimeStore

DEFAULT_TIMEOUT_S = 15
MAX_DISCOVERY_MODELS = 200


@dataclass(frozen=True, slots=True)
class ConnectionTestResult:
    gateway_id: str
    ok: bool
    http_status: int | None
    models_seen: int | None
    error_code: str | None
    checked_at_note: str = "backend-side check; no credential was exposed"


@dataclass(frozen=True, slots=True)
class DiscoveredModel:
    model_id: str


class AiRuntimeService:
    """Own AI gateway configuration; adapters consume the active gateway."""

    def __init__(self, store=None, secrets: SecretResolver | None = None) -> None:
        self.store = store if store is not None else InMemoryAiRuntimeStore()
        self.secrets = secrets if secrets is not None else SecretResolver()

    def current(self) -> AiRuntimeView:
        gateways = self.store.list_gateways()
        active = self.store.active_gateway_id()
        return AiRuntimeView(
            gateways=tuple(self._view(item, item.gateway_id == active) for item in gateways),
            active_gateway_id=active,
        )

    def active_gateway(self) -> GatewayConfig | None:
        active = self.store.active_gateway_id()
        if active is None:
            return None
        config = self.store.get_gateway(active)
        return config if config is not None and config.enabled else None

    def save_gateway(
        self,
        principal: object,
        config: GatewayConfig,
        *,
        actor_id: UUID | None = None,
        correlation_id: str | None = None,
    ) -> GatewayConfig:
        require_capability(principal, Capability.MANAGE_CONFIGURATION)
        known = {item.gateway_id for item in self.store.list_gateways()} | {config.gateway_id}
        validate_gateway(config, known)
        if actor_id is None:
            # audit_log.actor_id references persons; a principal_id is not a person.
            actor_id = getattr(principal, "person_id", None)
        if not config.enabled and config.gateway_id == self.store.active_gateway_id():
            raise AiConfigError("the active gateway cannot be disabled; activate another gateway first")
        if isinstance(self.store, PostgresAiRuntimeStore):
            return self.store.save_gateway(config, actor_id=actor_id, correlation_id=correlation_id)
        return self.store.save_gateway(config)

    def set_active(
        self,
        principal: object,
        gateway_id: str,
        *,
        actor_id: UUID | None = None,
        correlation_id: str | None = None,
    ) -> GatewayConfig:
        require_capability(principal, Capability.MANAGE_CONFIGURATION)
        config = self.store.get_gateway(gateway_id)
        if config is None:
            raise AiConfigError("unknown gateway")
        if actor_id is None:
            actor_id = getattr(principal, "person_id", None)
        if not config.enabled:
            raise AiConfigError("a disabled gateway cannot become active")
        known = {item.gateway_id for item in self.store.list_gateways()}
        validate_gateway(config, known)
        # Enabling a gateway never activates it; activation is always explicit.
        if isinstance(self.store, PostgresAiRuntimeStore):
            self.store.set_active(gateway_id, actor_id=actor_id, correlation_id=correlation_id)
        else:
            self.store.set_active(gateway_id)
        return config

    def test_connection(
        self,
        principal: object,
        gateway_id: str,
        *,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> ConnectionTestResult:
        require_capability(principal, Capability.MANAGE_CONFIGURATION)
        config = self._required_enabled(gateway_id)
        return self._probe(config, timeout_s=timeout_s)

    def discover_models(
        self,
        principal: object,
        gateway_id: str,
        *,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> tuple[DiscoveredModel, ...]:
        require_capability(principal, Capability.MANAGE_CONFIGURATION)
        config = self._required_enabled(gateway_id)
        body, _ = self._get_json(config, "models", timeout_s=timeout_s)
        data = body.get("data", []) if isinstance(body, dict) else []
        models: list[DiscoveredModel] = []
        for entry in data:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                models.append(DiscoveredModel(model_id=entry["id"]))
            if len(models) >= MAX_DISCOVERY_MODELS:
                break
        return tuple(models)

    def _required_enabled(self, gateway_id: str) -> GatewayConfig:
        config = self.store.get_gateway(gateway_id)
        if config is None:
            raise AiConfigError("unknown gateway")
        if not config.enabled:
            raise AiConfigError("gateway is disabled")
        return config

    def _view(self, config: GatewayConfig, is_active: bool) -> GatewayView:
        return GatewayView(
            gateway_id=config.gateway_id,
            display_name=config.display_name,
            gateway_type=config.gateway_type,
            endpoint=config.endpoint,
            auth_mode=config.auth_mode,
            route=config.route,
            enabled=config.enabled,
            is_local=config.is_local,
            fallback_gateway_id=config.fallback_gateway_id,
            config_version=config.config_version,
            credential_configured=self.secrets.credential_configured(config.secret_ref)
            if config.secret_ref is not None
            else True,
            last_test_at=config.last_test_at,
            last_test_ok=config.last_test_ok,
            is_active=is_active,
        )

    def _headers(self, config: GatewayConfig) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if config.secret_ref is not None:
            try:
                headers["Authorization"] = "Bearer " + self.secrets.resolve(config.secret_ref)
            except SecretMissing:
                raise AiConfigError("gateway credential is not configured")
        return headers

    def _get_json(self, config: GatewayConfig, path: str, *, timeout_s: int) -> tuple[dict, int | None]:
        url = config.endpoint.rstrip("/") + "/" + path.lstrip("/")
        request = urllib.request.Request(url, headers=self._headers(config), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                raw = response.read(1_000_000)
                return json.loads(raw.decode("utf-8")), response.status
        except urllib.error.HTTPError as exc:
            raise AiConfigError(f"gateway refused the request (http {exc.code})") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
            raise AiConfigError(f"gateway is unreachable: {type(exc).__name__}") from exc
        except (ValueError, UnicodeDecodeError) as exc:
            raise AiConfigError("gateway returned an unreadable response") from exc

    def _probe(self, config: GatewayConfig, *, timeout_s: int) -> ConnectionTestResult:
        try:
            body, status = self._get_json(config, "models", timeout_s=timeout_s)
        except AiConfigError as exc:
            message = str(exc)
            if "credential" in message or ("refused" in message and "401" in message):
                code = "auth_failure"
            elif "unreachable" in message:
                code = "connection_failure"
            else:
                code = "provider_failure"
            return ConnectionTestResult(
                gateway_id=config.gateway_id, ok=False, http_status=None,
                models_seen=None, error_code=code,
            )
        data = body.get("data", []) if isinstance(body, dict) else []
        count = len(data) if isinstance(data, list) else 0
        return ConnectionTestResult(
            gateway_id=config.gateway_id, ok=True, http_status=status,
            models_seen=count, error_code=None,
        )
