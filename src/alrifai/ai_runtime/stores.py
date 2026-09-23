"""Persistence for the canonical AI runtime configuration.

Postgres layout (V010) mirrors the frozen dataclasses; the in-memory store
covers tests and environments without the migration applied.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from ..services._common import all_rows, in_transaction, one, write_audit
from .config import GatewayAuthMode, GatewayConfig, GatewayType

AUDIT_ENTITY = "ai_gateway_config"


def _gateway_uuid(gateway_id: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"alrifai:ai-gateway:{gateway_id}")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryAiRuntimeStore:
    """Non-persistent store. Test and no-migration fallback only."""

    def __init__(self) -> None:
        self._gateways: dict[str, GatewayConfig] = {}
        self._active: str | None = None

    def list_gateways(self) -> tuple[GatewayConfig, ...]:
        return tuple(sorted(self._gateways.values(), key=lambda item: item.gateway_id))

    def get_gateway(self, gateway_id: str) -> GatewayConfig | None:
        return self._gateways.get(gateway_id)

    def save_gateway(self, config: GatewayConfig) -> GatewayConfig:
        stored = GatewayConfig(
            gateway_id=config.gateway_id,
            display_name=config.display_name,
            gateway_type=config.gateway_type,
            endpoint=config.endpoint,
            auth_mode=config.auth_mode,
            secret_ref=config.secret_ref,
            route=config.route,
            enabled=config.enabled,
            is_local=config.is_local,
            fallback_gateway_id=config.fallback_gateway_id,
            config_version=config.config_version,
            updated_by=config.updated_by,
            updated_at=config.updated_at or _utcnow(),
            last_test_at=config.last_test_at,
            last_test_ok=config.last_test_ok,
        )
        self._gateways[stored.gateway_id] = stored
        return stored

    def active_gateway_id(self) -> str | None:
        return self._active

    def set_active(self, gateway_id: str | None) -> None:
        self._active = gateway_id


class PostgresAiRuntimeStore:
    """DB-API adapter over the V010 ai_gateway_configs / ai_runtime_state tables."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def list_gateways(self) -> tuple[GatewayConfig, ...]:
        rows = all_rows(
            self.connection,
            "SELECT gateway_id, display_name, gateway_type, endpoint, auth_mode,"
            " secret_ref, route, enabled, is_local, fallback_gateway_id,"
            " config_version, updated_by, updated_at, last_test_at, last_test_ok"
            " FROM ai_gateway_configs ORDER BY gateway_id",
        )
        return tuple(_config_from_row(row) for row in rows)

    def get_gateway(self, gateway_id: str) -> GatewayConfig | None:
        row = one(
            self.connection,
            "SELECT gateway_id, display_name, gateway_type, endpoint, auth_mode,"
            " secret_ref, route, enabled, is_local, fallback_gateway_id,"
            " config_version, updated_by, updated_at, last_test_at, last_test_ok"
            " FROM ai_gateway_configs WHERE gateway_id=%s",
            (gateway_id,),
        )
        return _config_from_row(row) if row else None

    def save_gateway(
        self,
        config: GatewayConfig,
        *,
        actor_id: UUID | None,
        correlation_id: str | None,
    ) -> GatewayConfig:
        def _save() -> GatewayConfig:
            before = self.get_gateway(config.gateway_id)
            stored_at = _utcnow()
            one(
                self.connection,
                "INSERT INTO ai_gateway_configs (gateway_id, display_name, gateway_type,"
                " endpoint, auth_mode, secret_ref, route, enabled, is_local,"
                " fallback_gateway_id, config_version, updated_by, updated_at,"
                " last_test_at, last_test_ok)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " ON CONFLICT (gateway_id) DO UPDATE SET display_name=EXCLUDED.display_name,"
                " gateway_type=EXCLUDED.gateway_type, endpoint=EXCLUDED.endpoint,"
                " auth_mode=EXCLUDED.auth_mode, secret_ref=EXCLUDED.secret_ref,"
                " route=EXCLUDED.route, enabled=EXCLUDED.enabled, is_local=EXCLUDED.is_local,"
                " fallback_gateway_id=EXCLUDED.fallback_gateway_id,"
                " config_version=EXCLUDED.config_version, updated_by=EXCLUDED.updated_by,"
                " updated_at=EXCLUDED.updated_at, last_test_at=EXCLUDED.last_test_at,"
                " last_test_ok=EXCLUDED.last_test_ok"
                " RETURNING gateway_id",
                (
                    config.gateway_id, config.display_name, config.gateway_type.value,
                    config.endpoint, config.auth_mode.value, config.secret_ref,
                    config.route, config.enabled, config.is_local,
                    config.fallback_gateway_id, config.config_version,
                    config.updated_by, stored_at, config.last_test_at, config.last_test_ok,
                ),
            )
            stored = self.get_gateway(config.gateway_id)
            assert stored is not None
            write_audit(
                self.connection,
                entity_type=AUDIT_ENTITY,
                entity_id=_gateway_uuid(config.gateway_id),
                action="CREATE" if before is None else "UPDATE",
                actor_id=actor_id,
                before=None if before is None else {"route": before.route, "enabled": before.enabled},
                after={"route": stored.route, "enabled": stored.enabled, "endpoint": stored.endpoint},
                correlation_id=correlation_id,
            )
            return stored

        return in_transaction(self.connection, _save)

    def active_gateway_id(self) -> str | None:
        row = one(self.connection, "SELECT active_gateway_id FROM ai_runtime_state WHERE singleton_id=1")
        return str(row[0]) if row and row[0] is not None else None

    def set_active(
        self,
        gateway_id: str | None,
        *,
        actor_id: UUID | None,
        correlation_id: str | None,
    ) -> None:
        def _set() -> None:
            one(
                self.connection,
                "UPDATE ai_runtime_state SET active_gateway_id=%s WHERE singleton_id=1"
                " RETURNING singleton_id",
                (gateway_id,),
            )
            write_audit(
                self.connection,
                entity_type="ai_runtime_state",
                entity_id=uuid5(NAMESPACE_URL, "alrifai:ai-runtime-state"),
                action="UPDATE",
                actor_id=actor_id,
                before=None,
                after={"active_gateway_id": gateway_id},
                correlation_id=correlation_id,
            )

        in_transaction(self.connection, _set)


def _config_from_row(row: Sequence[object]) -> GatewayConfig:
    return GatewayConfig(
        gateway_id=str(row[0]),
        display_name=str(row[1]),
        gateway_type=GatewayType(str(row[2])),
        endpoint=str(row[3]),
        auth_mode=GatewayAuthMode(str(row[4])),
        secret_ref=str(row[5]) if row[5] is not None else None,
        route=str(row[6]),
        enabled=bool(row[7]),
        is_local=bool(row[8]),
        fallback_gateway_id=str(row[9]) if row[9] is not None else None,
        config_version=int(row[10]),
        updated_by=str(row[11]) if row[11] is not None else None,
        updated_at=row[12],  # type: ignore[arg-type]
        last_test_at=row[13],  # type: ignore[arg-type]
        last_test_ok=bool(row[14]) if row[14] is not None else None,
    )
