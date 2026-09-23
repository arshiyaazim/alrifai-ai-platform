"""Pure contract tests for the Owner/Admin authority foundation."""

from uuid import uuid4

import pytest

from src.alrifai.authorization.policy import (
    ALL_BUSINESS_CAPABILITIES,
    OWNER_ONLY_CAPABILITIES,
    AuthenticationMethod,
    AuthorizationDenied,
    AssuranceLevel,
    Capability,
    PrincipalType,
    TrustedPrincipal,
    _from_verified_authentication,
    authorize,
    require_capability,
)


def _owner():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.OWNER,
        person_id=uuid4(),
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.frontend",
        assurance=AssuranceLevel.HIGH,
        capabilities=frozenset(),
    )


def _ordinary_admin():
    return _from_verified_authentication(
        principal_id=uuid4(),
        principal_type=PrincipalType.ADMIN,
        person_id=uuid4(),
        authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
        source="test.frontend",
        assurance=AssuranceLevel.STANDARD,
        capabilities=frozenset({Capability.VIEW_REPORTS}),
    )


def test_owner_has_full_authority_independent_of_delegated_permissions():
    owner = _owner()

    assert {authorize(owner, capability).allowed for capability in ALL_BUSINESS_CAPABILITIES} == {True}
    assert require_capability(owner, Capability.MANAGE_CONFIGURATION).principal_id == owner.principal_id


def test_owner_is_distinct_from_canonical_person_and_role_claims():
    owner = _owner()
    ordinary = _ordinary_admin()

    assert owner.principal_type is PrincipalType.OWNER
    assert owner.principal_id != ordinary.principal_id
    assert owner.person_id != ordinary.person_id
    assert authorize(ordinary, Capability.MANAGE_CONFIGURATION).allowed is False


def test_ordinary_person_cannot_impersonate_owner():
    ordinary = _ordinary_admin()

    for capability in OWNER_ONLY_CAPABILITIES:
        decision = authorize(ordinary, capability)
        assert decision.allowed is False
        assert decision.reason == "owner authority required"


def test_raw_person_id_or_role_claim_cannot_authorize():
    untrusted_claims = {
        "person_id": str(uuid4()),
        "principal_type": "owner",
        "role": "owner",
        "capabilities": [Capability.MANAGE_CONFIGURATION.value],
    }

    decision = authorize(untrusted_claims, Capability.MANAGE_CONFIGURATION)

    assert decision.allowed is False
    assert decision.principal_id is None
    with pytest.raises(AuthorizationDenied, match="trusted principal required"):
        require_capability(untrusted_claims, Capability.MANAGE_CONFIGURATION)


def test_public_constructor_cannot_forge_trusted_owner():
    with pytest.raises(AuthorizationDenied, match="verified authentication adapter"):
        TrustedPrincipal(
            construction_token=object(),
            principal_id=uuid4(),
            principal_type=PrincipalType.OWNER,
            person_id=uuid4(),
            authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
            source="untrusted.request",
            assurance=AssuranceLevel.HIGH,
            capabilities=ALL_BUSINESS_CAPABILITIES,
        )


def test_owner_requires_high_assurance_at_the_authentication_boundary():
    with pytest.raises(AuthorizationDenied, match="high assurance"):
        _from_verified_authentication(
            principal_id=uuid4(),
            principal_type=PrincipalType.OWNER,
            person_id=uuid4(),
            authentication_method=AuthenticationMethod.VERIFIED_WHATSAPP_CHANNEL,
            source="test.whatsapp",
            assurance=AssuranceLevel.STANDARD,
            capabilities=frozenset(),
        )
