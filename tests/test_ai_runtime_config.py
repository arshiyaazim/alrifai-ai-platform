"""Focused tests for the canonical AI runtime configuration service."""

from uuid import uuid4

import pytest

from alrifai.ai_runtime.config import (
    AiConfigError,
    GatewayAuthMode,
    GatewayConfig,
    GatewayType,
    validate_gateway,
)
from alrifai.ai_runtime.secrets import SecretMissing, SecretResolver
from alrifai.ai_runtime.service import AiRuntimeService
from alrifai.ai_runtime.stores import InMemoryAiRuntimeStore
from alrifai.authorization.policy import (
    AssuranceLevel,
    AuthenticationMethod,
    AuthorizationDenied,
    Capability,
    PrincipalType,
    _from_verified_authentication,
)


def _owner():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.OWNER,
        person_id=None,
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.ai-runtime",
        assurance=AssuranceLevel.HIGH,
        capabilities=frozenset(),
    )


def _staff():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.ADMIN,
        person_id=uuid4(),
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.ai-runtime",
        assurance=AssuranceLevel.STANDARD,
        capabilities=frozenset({Capability.MANAGE_APPLICANTS}),
    )


def _gateway(**overrides):
    base = {
        "gateway_id": "nine-general",
        "display_name": "9Router general",
        "gateway_type": GatewayType.NINE_ROUTER,
        "endpoint": "http://127.0.0.1:20129/v1",
        "auth_mode": GatewayAuthMode.API_KEY,
        "secret_ref": "env:TEST_NINEROUTER_KEY",
        "route": "general",
        "enabled": True,
        "is_local": False,
    }
    base.update(overrides)
    return GatewayConfig(**base)


def _service(env=None):
    return AiRuntimeService(
        store=InMemoryAiRuntimeStore(),
        secrets=SecretResolver(environ=dict(env or {})),
    )


def test_valid_gateway_passes_validation():
    validate_gateway(_gateway(), {"nine-general"})


def test_endpoint_must_be_http_without_credentials():
    for bad in ["", "ftp://host/v1", "http://user:pass@host/v1", "not-a-url", "http:///v1"]:
        with pytest.raises(AiConfigError):
            validate_gateway(_gateway(endpoint=bad), {"nine-general"})


def test_api_key_gateway_requires_secret_ref():
    with pytest.raises(AiConfigError):
        validate_gateway(_gateway(secret_ref=None), {"nine-general"})
    with pytest.raises(AiConfigError):
        validate_gateway(_gateway(secret_ref="plaintext-key"), {"nine-general"})


def test_none_auth_must_not_carry_secret_ref():
    with pytest.raises(AiConfigError):
        validate_gateway(
            _gateway(auth_mode=GatewayAuthMode.NONE, secret_ref="env:X"),
            {"nine-general"},
        )


def test_fallback_cannot_be_self_or_unknown():
    with pytest.raises(AiConfigError):
        validate_gateway(_gateway(fallback_gateway_id="nine-general"), {"nine-general"})
    with pytest.raises(AiConfigError):
        validate_gateway(_gateway(fallback_gateway_id="missing"), {"nine-general", "other"})
    validate_gateway(_gateway(fallback_gateway_id="other"), {"nine-general", "other"})


def test_non_owner_cannot_save_or_activate():
    service = _service()
    with pytest.raises(AuthorizationDenied):
        service.save_gateway(_staff(), _gateway())
    service.save_gateway(_owner(), _gateway())
    with pytest.raises(AuthorizationDenied):
        service.set_active(_staff(), "nine-general")
    with pytest.raises(AuthorizationDenied):
        service.test_connection(_staff(), "nine-general")


def test_invalid_config_cannot_be_saved_or_activated():
    service = _service()
    with pytest.raises(AiConfigError):
        service.save_gateway(_owner(), _gateway(endpoint="ftp://bad/v1"))
    assert service.current().gateways == ()


def test_disabled_gateway_cannot_become_active():
    service = _service()
    service.save_gateway(_owner(), _gateway(enabled=False))
    with pytest.raises(AiConfigError):
        service.set_active(_owner(), "nine-general")
    assert service.current().active_gateway_id is None


def test_active_gateway_cannot_be_disabled_in_place():
    service = _service()
    owner = _owner()
    service.save_gateway(owner, _gateway())
    service.set_active(owner, "nine-general")
    with pytest.raises(AiConfigError):
        service.save_gateway(owner, _gateway(enabled=False))


def test_enabling_does_not_auto_activate():
    service = _service()
    owner = _owner()
    service.save_gateway(owner, _gateway(enabled=False))
    service.save_gateway(owner, _gateway(enabled=True))
    assert service.current().active_gateway_id is None


def test_activation_switches_runtime_truth():
    service = _service()
    owner = _owner()
    service.save_gateway(owner, _gateway())
    service.save_gateway(owner, _gateway(gateway_id="local", display_name="Local",
                                         gateway_type=GatewayType.OLLAMA,
                                         endpoint="http://127.0.0.1:11434/v1",
                                         auth_mode=GatewayAuthMode.NONE,
                                         secret_ref=None, route="local-model",
                                         is_local=True))
    service.set_active(owner, "nine-general")
    assert service.active_gateway().gateway_id == "nine-general"
    service.set_active(owner, "local")
    assert service.active_gateway().gateway_id == "local"


def test_view_never_carries_credential_values():
    secret_value = "super-secret-credential-value"
    service = _service(env={"TEST_NINEROUTER_KEY": secret_value})
    service.save_gateway(_owner(), _gateway())
    view = service.current()
    assert len(view.gateways) == 1
    rendered = repr(view)
    assert secret_value not in rendered
    assert view.gateways[0].credential_configured is True
    missing = _service(env={})
    missing.save_gateway(_owner(), _gateway())
    assert missing.current().gateways[0].credential_configured is False


def test_missing_credential_blocks_probe_with_clear_error():
    service = _service(env={})
    service.save_gateway(_owner(), _gateway())
    result = service.test_connection(_owner(), "nine-general")
    assert result.ok is False
    assert result.error_code == "auth_failure"


def test_resolver_supports_env_and_file(tmp_path):
    secret_file = tmp_path / "nine.key"
    secret_file.write_text("file-secret\n", encoding="utf-8")
    resolver = SecretResolver(environ={})
    assert resolver.resolve(f"file:{secret_file}") == "file-secret"
    with pytest.raises(SecretMissing):
        resolver.resolve("env:ABSENT_VAR")
    with pytest.raises(SecretMissing):
        resolver.resolve("vault:key")
