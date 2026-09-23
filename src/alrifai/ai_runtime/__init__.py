"""Canonical AI runtime configuration.

One configuration service owns which approved gateway/route the backend AI
runtime (including C7) uses. The Web UI and any future MCP/admin surface are
adapters over this service; there is no second source of truth.
"""

from .config import (
    AiConfigError,
    AiRuntimeView,
    GatewayAuthMode,
    GatewayConfig,
    GatewayType,
    GatewayView,
    validate_gateway,
)
from .secrets import SecretMissing, SecretResolver
from .service import AiRuntimeService, ConnectionTestResult, DiscoveredModel
from .stores import InMemoryAiRuntimeStore, PostgresAiRuntimeStore

__all__ = [
    "AiConfigError",
    "AiRuntimeService",
    "AiRuntimeView",
    "ConnectionTestResult",
    "DiscoveredModel",
    "GatewayAuthMode",
    "GatewayConfig",
    "GatewayType",
    "GatewayView",
    "InMemoryAiRuntimeStore",
    "PostgresAiRuntimeStore",
    "SecretMissing",
    "SecretResolver",
    "validate_gateway",
]
