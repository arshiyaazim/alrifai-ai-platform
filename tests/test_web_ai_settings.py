"""Focused tests for the Admin AI/model settings Web UI.

The backend runtime configuration is the single source of truth: the page
renders backend state, changes flow through the canonical service, browsers
never receive credentials, and unauthorized users cannot modify anything.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import src.alrifai.web.app as webapp
from src.alrifai.ai_runtime.service import AiRuntimeService
from src.alrifai.ai_runtime.stores import InMemoryAiRuntimeStore
from src.alrifai.ai_runtime.secrets import SecretResolver
from src.alrifai.auth.service import _hash_token
from src.alrifai.authorization.policy import (
    AssuranceLevel,
    AuthenticationMethod,
    PrincipalType,
    _from_verified_authentication,
)

SECRET_VALUE = "web-test-credential-value"
CSRF_TOKEN = "test-csrf-token"


def _owner():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.OWNER,
        person_id=None,
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.web-ai-settings",
        assurance=AssuranceLevel.HIGH,
        capabilities=frozenset(),
    )


@pytest.fixture()
def client(monkeypatch):
    from contextlib import contextmanager

    service = AiRuntimeService(
        store=InMemoryAiRuntimeStore(),
        secrets=SecretResolver(environ={"WEB_TEST_KEY": SECRET_VALUE}),
    )
    principal = _owner()
    monkeypatch.setattr(webapp, "_session", lambda request: (principal, _hash_token(CSRF_TOKEN)))

    @contextmanager
    def _fake_database():
        yield object()

    monkeypatch.setattr(webapp, "database", _fake_database)
    monkeypatch.setattr(webapp, "_ai_service", lambda connection: (service, None))
    return TestClient(webapp.app, raise_server_exceptions=False), service


def _post(client, path, **fields):
    data = {"csrf_token": CSRF_TOKEN}
    data.update(fields)
    return client.post(path, data=data, follow_redirects=False)


def test_page_loads_backend_state(client):
    http, _ = client
    response = http.get("/admin/ai-settings")
    assert response.status_code == 200
    assert "No gateways configured" in response.text
    assert SECRET_VALUE not in response.text


def test_save_then_activate_changes_runtime_truth(client):
    http, service = client
    saved = _post(
        http, "/admin/ai-settings/save", gateway_id="nine-general",
        display_name="9Router general", gateway_type="nine_router",
        endpoint="http://127.0.0.1:20129/v1", auth_mode="api_key",
        secret_ref="env:WEB_TEST_KEY", route="general", enabled="on",
    )
    assert saved.status_code == 303
    assert service.active_gateway() is None
    activated = _post(http, "/admin/ai-settings/set-active", gateway_id="nine-general")
    assert activated.status_code == 303
    assert service.active_gateway().gateway_id == "nine-general"
    page = http.get("/admin/ai-settings")
    assert "nine-general" in page.text
    assert "active" in page.text
    assert SECRET_VALUE not in page.text


def test_invalid_configuration_cannot_become_active(client):
    http, service = client
    rejected = _post(
        http, "/admin/ai-settings/save", gateway_id="bad",
        display_name="Bad", gateway_type="nine_router",
        endpoint="ftp://bad/v1", auth_mode="api_key",
        secret_ref="env:WEB_TEST_KEY", route="general", enabled="on",
    )
    assert rejected.status_code == 200
    assert "rejected" in rejected.text
    assert service.current().gateways == ()


def test_unauthorized_users_cannot_modify(client, monkeypatch):
    http, service = client
    monkeypatch.setattr(webapp, "_session", lambda request: None)
    assert http.get("/admin/ai-settings", follow_redirects=False).status_code == 303
    response = _post(
        http, "/admin/ai-settings/save", gateway_id="x", display_name="X",
        gateway_type="nine_router", endpoint="http://127.0.0.1:20129/v1",
        auth_mode="api_key", secret_ref="env:WEB_TEST_KEY", route="general",
        enabled="on",
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert service.current().gateways == ()


def test_csrf_mismatch_is_rejected(client):
    http, service = client
    response = http.post("/admin/ai-settings/save", data={
        "csrf_token": "wrong", "gateway_id": "x", "display_name": "X",
        "gateway_type": "nine_router", "endpoint": "http://127.0.0.1:20129/v1",
        "auth_mode": "api_key", "secret_ref": "env:WEB_TEST_KEY",
        "route": "general", "enabled": "on",
    })
    assert response.status_code == 200
    assert "Invalid session token" in response.text
    assert service.current().gateways == ()


def test_connection_test_reports_backend_result_without_secrets(client, monkeypatch):
    http, _ = client

    class Probe:
        gateway_id = "nine-general"

        def __init__(self):
            self.ok = False
            self.error_code = "connection_failure"

    monkeypatch.setattr(AiRuntimeService, "test_connection",
                        lambda self, principal, gateway_id, **kwargs: Probe())
    saved = _post(
        http, "/admin/ai-settings/save", gateway_id="nine-general",
        display_name="9Router general", gateway_type="nine_router",
        endpoint="http://127.0.0.1:9/v1", auth_mode="api_key",
        secret_ref="env:WEB_TEST_KEY", route="general", enabled="on",
    )
    assert saved.status_code == 303
    response = _post(http, "/admin/ai-settings/test", gateway_id="nine-general")
    assert response.status_code == 200
    assert "connection_failure" in response.text
    assert SECRET_VALUE not in response.text
