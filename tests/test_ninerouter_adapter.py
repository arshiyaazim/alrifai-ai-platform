"""Focused tests for the C7 OpenAI-compatible interpretation adapter.

A scripted fake gateway emulates 9Router/OpenAI wire behavior so failure
classification, bounds, and the live C7 contract are verified without any
real provider, credential, or network dependency.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

import pytest

from alrifai.ai_runtime.config import GatewayAuthMode, GatewayConfig, GatewayType
from alrifai.ai_runtime.secrets import SecretResolver
from alrifai.ai_runtime.service import AiRuntimeService
from alrifai.ai_runtime.stores import InMemoryAiRuntimeStore
from alrifai.authorization.policy import (
    AssuranceLevel,
    AuthenticationMethod,
    PrincipalType,
    _from_verified_authentication,
)
from alrifai.conversations.interpretation import (
    FailureReason,
    HermesAdapterResponse,
    HermesProviderError,
    InterpretationRequest,
    InterpretationService,
    InterpretationStatus,
    SCHEMA_VERSION,
)
from alrifai.conversations.ninerouter_adapter import (
    NineRouterInterpretationAdapter,
    ResolvedRoute,
)
from test_conversation_interpretation import context_for, output


SECRET = "test-adapter-credential"


def _owner():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.OWNER,
        person_id=None,
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.c7-adapter",
        assurance=AssuranceLevel.HIGH,
        capabilities=frozenset(),
    )


def _service_with_active(route="general", env=None):
    service = AiRuntimeService(
        store=InMemoryAiRuntimeStore(),
        secrets=SecretResolver(environ=dict(env if env is not None else {"TEST_ADAPTER_KEY": SECRET})),
    )
    service.save_gateway(
        _owner(),
        GatewayConfig(
            gateway_id="nine-test", display_name="Test gateway",
            gateway_type=GatewayType.NINE_ROUTER, endpoint="http://127.0.0.1:1/v1",
            auth_mode=GatewayAuthMode.API_KEY, secret_ref="env:TEST_ADAPTER_KEY",
            route=route, enabled=True, is_local=False,
        ),
    )
    service.set_active(_owner(), "nine-test")
    return service


class FakeGateway:
    """Scripted OpenAI-compatible endpoint running on loopback."""

    def __init__(self, handler):
        self.requests = []
        self._handler = handler
        self._server = HTTPServer(("127.0.0.1", 0), self._make_handler())
        self.thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def _make_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                outer.requests.append({
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                    "correlation": self.headers.get("X-Correlation-Id"),
                    "body": raw,
                })
                outer._handler(self, raw)

            def do_GET(self):
                outer.requests.append({"path": self.path, "method": "GET"})
                outer._handler(self, b"")

        return Handler

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self._server.shutdown()
        self.thread.join(timeout=5)


def _c7_envelope(content, model="test-model"):
    return {"id": "chatcmpl-test", "model": model,
            "choices": [{"message": {"role": "assistant", "content": content}}]}


def _respond(handler, status, payload, content_type="application/json"):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _adapter_for(server, **overrides):
    route = ResolvedRoute(gateway_id="nine-test", endpoint=server.url + "/v1",
                          route="general", api_key=SECRET)
    return NineRouterInterpretationAdapter(route, **overrides)


def test_success_posts_model_route_with_json_object_and_auth():
    package, _, _, current = context_for()
    envelope = _c7_envelope(json.dumps(output(
        language_evidence=["bangla"], language_confidence=0.9,
        intent_hypotheses=[{"label": "ask_suitability", "domain": "recruitment",
                             "confidence": 0.8, "message_ids": [str(current.message_id)],
                             "turn_ids": [str(item.turn_id) for item in package.turns]}],
    )))

    def handler(server, raw):
        _respond(server, 200, envelope)

    with FakeGateway(handler) as server:
        adapter = _adapter_for(server, correlation_id="corr-1")
        result = InterpretationService(adapter).interpret(InterpretationRequest(context=package))

    assert result.status is InterpretationStatus.INTERPRETED
    assert result.model_route == "nine-test/general"
    assert result.model_version == "test-model"
    assert result.failure_reason is None
    sent = server.requests[0]
    assert sent["path"] == "/v1/chat/completions"
    assert sent["authorization"] == "Bearer " + SECRET
    assert sent["correlation"] == "corr-1"
    body = json.loads(sent["body"])
    assert body["model"] == "general"
    assert body["response_format"] == {"type": "json_object"}


def test_no_route_is_hardcoded_in_adapter():
    import alrifai.conversations.ninerouter_adapter as module

    source = open(module.__file__, encoding="utf-8").read()
    assert '"general"' not in source and "'general'" not in source


def test_unauthorized_gateway_becomes_typed_provider_error():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 401, {"error": "unauthorized"})

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server)).interpret(
            InterpretationRequest(context=package))
    assert result.status is InterpretationStatus.ABSTAINED
    assert result.failure_reason is FailureReason.AUTHENTICATION
    assert len(server.requests) == 1


def test_provider_outage_becomes_typed_provider_error():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 500, {"error": "overloaded"})

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server)).interpret(
            InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.PROVIDER_ERROR


def test_unreadable_output_becomes_provider_error():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 200, b"not json{{{", content_type="text/plain")

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server)).interpret(
            InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.MALFORMED_RESPONSE
    assert len(server.requests) == 1


def test_schema_invalid_json_reaches_c7_validation_as_malformed():
    package, _, _, _ = context_for()
    envelope = _c7_envelope(json.dumps({"wrong": "shape"}))

    def handler(server, raw):
        _respond(server, 200, envelope)

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server)).interpret(
            InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.MALFORMED_OUTPUT


def test_timeout_is_classified_without_mutation():
    import time

    package, _, _, _ = context_for()

    def handler(server, raw):
        time.sleep(3)
        try:
            _respond(server, 200, _c7_envelope("{}"))
        except (BrokenPipeError, ConnectionResetError):
            pass

    with FakeGateway(handler) as server:
        adapter = _adapter_for(server, timeout_s=1)
        result = InterpretationService(adapter).interpret(InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.MODEL_TIMEOUT


def test_missing_active_config_fails_closed():
    service = AiRuntimeService(store=InMemoryAiRuntimeStore())
    with pytest.raises(HermesProviderError):
        NineRouterInterpretationAdapter.from_active_config(service)


def test_missing_credential_fails_closed_without_leak():
    service = _service_with_active(env={})
    with pytest.raises(HermesProviderError) as excinfo:
        NineRouterInterpretationAdapter.from_active_config(service)
    assert SECRET not in str(excinfo.value)


def test_from_active_config_consumes_backend_truth():
    service = _service_with_active(route="coding")
    adapter = NineRouterInterpretationAdapter.from_active_config(service)
    assert adapter.route.route == "coding"
    assert adapter.route.api_key == SECRET


def test_error_text_never_contains_credential():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 403, {"error": "forbidden"})

    with FakeGateway(handler) as server:
        try:
            _adapter_for(server).interpret({"too": "large" * 100000})
        except HermesProviderError as exc:
            assert SECRET not in str(exc)
        result = InterpretationService(_adapter_for(server)).interpret(
            InterpretationRequest(context=package))
    assert SECRET not in (result.uncertainty[0] if result.uncertainty else "")



def test_transient_failure_recovers_with_one_bounded_retry():
    package, _, _, _ = context_for()
    calls = []

    def handler(server, raw):
        calls.append(1)
        if len(calls) == 1:
            _respond(server, 503, {"error": "busy"})
        else:
            _respond(server, 200, _c7_envelope(json.dumps(output())))

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server, retry_delay_s=0)).interpret(
            InterpretationRequest(context=package))
    assert result.status is InterpretationStatus.INTERPRETED
    assert len(server.requests) == 2


def test_retry_exhaustion_is_bounded_and_typed():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 503, {"error": "busy"})

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server, retry_delay_s=0)).interpret(
            InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.PROVIDER_ERROR
    assert len(server.requests) == 2


def test_non_retryable_authentication_failure_is_not_retried():
    package, _, _, _ = context_for()

    def handler(server, raw):
        _respond(server, 401, {"error": "unauthorized"})

    with FakeGateway(handler) as server:
        result = InterpretationService(_adapter_for(server, retry_delay_s=0)).interpret(
            InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.AUTHENTICATION
    assert len(server.requests) == 1


def test_unreachable_provider_is_distinct_from_timeout():
    package, _, _, _ = context_for()
    adapter = NineRouterInterpretationAdapter(
        ResolvedRoute("nine-test", "http://127.0.0.1:1/v1", "general", SECRET),
        timeout_s=1, retry_delay_s=0,
    )
    result = InterpretationService(adapter).interpret(InterpretationRequest(context=package))
    assert result.failure_reason is FailureReason.UNREACHABLE_PROVIDER


def test_disabled_and_unknown_active_gateways_are_typed():
    service = AiRuntimeService(store=InMemoryAiRuntimeStore())
    with pytest.raises(HermesProviderError) as unknown:
        NineRouterInterpretationAdapter.from_active_config(service)
    assert unknown.value.reason is FailureReason.UNKNOWN_GATEWAY

    configured = _service_with_active()
    configured.store.save_gateway(GatewayConfig(
        gateway_id="disabled", display_name="Disabled", gateway_type=GatewayType.NINE_ROUTER,
        endpoint="http://127.0.0.1:1/v1", auth_mode=GatewayAuthMode.API_KEY,
        secret_ref="env:TEST_ADAPTER_KEY", route="general", enabled=False, is_local=False,
    ))
    configured.store.set_active("disabled")
    with pytest.raises(HermesProviderError) as disabled:
        NineRouterInterpretationAdapter.from_active_config(configured)
    assert disabled.value.reason is FailureReason.DISABLED_GATEWAY
