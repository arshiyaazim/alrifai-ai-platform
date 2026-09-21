"""Platform-wide authorization contracts and Owner semantics.

This module deliberately does not authenticate credentials or load roles from
the database. Authentication adapters must create ``TrustedPrincipal`` only
after verifying a credential, session, channel, or service identity. Domain
services and MCP adapters consume the resulting principal and never accept a
caller-supplied person ID or role claim as authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import FrozenSet
from uuid import UUID


class PrincipalType(StrEnum):
    """Platform identity classes, separate from canonical person identity."""

    OWNER = "owner"
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OFFICE_STAFF = "office_staff"
    OPERATIONS = "operations"
    ACCOUNTANT = "accountant"
    EMPLOYEE = "employee"
    APPLICANT = "applicant"
    CLIENT = "client"
    AI_SERVICE = "ai_service"


class AuthenticationMethod(StrEnum):
    """Authentication mechanisms recognized by the future adapters."""

    FRONTEND_PASSWORD = "frontend_password"
    VERIFIED_WHATSAPP_CHANNEL = "verified_whatsapp_channel"
    SERVICE_IDENTITY = "service_identity"


class AssuranceLevel(StrEnum):
    """Strength of the authentication evidence supplied by an adapter."""

    STANDARD = "standard"
    HIGH = "high"


class Capability(StrEnum):
    """Stable business capabilities used by domain services and MCP tools."""

    VIEW_ALL_BUSINESS_DATA = "view_all_business_data"
    VIEW_UNMASKED_CONTACTS = "view_unmasked_contacts"
    MANAGE_APPLICANTS = "manage_applicants"
    MANAGE_EMPLOYEES = "manage_employees"
    MANAGE_PAYROLL = "manage_payroll"
    MANAGE_CASH = "manage_cash"
    MANAGE_CONVERSATIONS = "manage_conversations"
    MANAGE_ESCORTS = "manage_escorts"
    VIEW_REPORTS = "view_reports"
    APPROVE_BUSINESS_OPERATIONS = "approve_business_operations"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"
    MANAGE_CONFIGURATION = "manage_configuration"
    HIRE_APPLICANT = "hire_applicant"
    MCP_ADMIN = "mcp_admin"


ALL_BUSINESS_CAPABILITIES: FrozenSet[Capability] = frozenset(Capability)

# These operations change who may act in the system or alter platform-wide
# security policy. Other roles may receive narrower user-management rights,
# but the Owner semantics remain independent of delegated permissions.
OWNER_ONLY_CAPABILITIES: FrozenSet[Capability] = frozenset(
    {
        Capability.MANAGE_ROLES,
        Capability.MANAGE_PERMISSIONS,
        Capability.MANAGE_CONFIGURATION,
    }
)


class AuthorizationDenied(PermissionError):
    """The supplied actor is not a trusted principal for the capability."""


class _TrustedConstructionToken:
    pass


_TRUSTED_CONSTRUCTION_TOKEN = _TrustedConstructionToken()


@dataclass(frozen=True, init=False)
class TrustedPrincipal:
    """Immutable output of a verified authentication adapter.

    The constructor is intentionally sealed. The authentication package will
    later expose adapter-specific verification functions that call the private
    construction boundary. A UUID, phone number, username, model argument, or
    role string cannot be converted into this object by an ordinary caller.
    """

    principal_id: UUID
    principal_type: PrincipalType
    person_id: UUID | None
    authentication_method: AuthenticationMethod
    source: str
    assurance: AssuranceLevel
    capabilities: FrozenSet[Capability]

    def __init__(
        self,
        *,
        construction_token: object,
        principal_id: UUID,
        principal_type: PrincipalType,
        person_id: UUID | None,
        authentication_method: AuthenticationMethod,
        source: str,
        assurance: AssuranceLevel,
        capabilities: FrozenSet[Capability],
    ) -> None:
        if construction_token is not _TRUSTED_CONSTRUCTION_TOKEN:
            raise AuthorizationDenied(
                "TrustedPrincipal must be created by a verified authentication adapter"
            )
        if not source.strip():
            raise ValueError("trusted principal source is required")
        if principal_type is PrincipalType.OWNER and assurance is not AssuranceLevel.HIGH:
            raise AuthorizationDenied("Owner authentication requires high assurance")
        object.__setattr__(self, "principal_id", principal_id)
        object.__setattr__(self, "principal_type", principal_type)
        object.__setattr__(self, "person_id", person_id)
        object.__setattr__(self, "authentication_method", authentication_method)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "assurance", assurance)
        object.__setattr__(self, "capabilities", frozenset(capabilities))


@dataclass(frozen=True)
class AuthorizationDecision:
    """Auditable result of a central capability decision."""

    allowed: bool
    capability: Capability
    principal_id: UUID | None
    reason: str


def authorize(
    principal: object,
    capability: Capability,
) -> AuthorizationDecision:
    """Evaluate one capability using only a trusted server-side principal.

    Owner is a distinct principal type and receives all defined capabilities;
    the result does not depend on the Owner's delegated permission set. Every
    other principal must have the capability resolved by the server-side
    authentication/authorization adapter.
    """
    if not isinstance(principal, TrustedPrincipal):
        return AuthorizationDecision(
            allowed=False,
            capability=capability,
            principal_id=None,
            reason="trusted principal required",
        )
    if principal.principal_type is PrincipalType.OWNER:
        return AuthorizationDecision(
            allowed=True,
            capability=capability,
            principal_id=principal.principal_id,
            reason="owner full authority",
        )
    if capability in OWNER_ONLY_CAPABILITIES:
        return AuthorizationDecision(
            allowed=False,
            capability=capability,
            principal_id=principal.principal_id,
            reason="owner authority required",
        )
    if capability in principal.capabilities:
        return AuthorizationDecision(
            allowed=True,
            capability=capability,
            principal_id=principal.principal_id,
            reason="delegated capability granted by server-side policy",
        )
    return AuthorizationDecision(
        allowed=False,
        capability=capability,
        principal_id=principal.principal_id,
        reason="capability not granted",
    )


def require_capability(principal: object, capability: Capability) -> AuthorizationDecision:
    """Return an allowed decision or raise without accepting caller claims."""
    decision = authorize(principal, capability)
    if not decision.allowed:
        raise AuthorizationDenied(decision.reason)
    return decision


def _from_verified_authentication(
    *,
    principal_id: UUID,
    principal_type: PrincipalType,
    person_id: UUID | None,
    authentication_method: AuthenticationMethod,
    source: str,
    assurance: AssuranceLevel,
    capabilities: FrozenSet[Capability],
) -> TrustedPrincipal:
    """Internal adapter boundary used by future verified auth implementations."""
    return TrustedPrincipal(
        construction_token=_TRUSTED_CONSTRUCTION_TOKEN,
        principal_id=principal_id,
        principal_type=principal_type,
        person_id=person_id,
        authentication_method=authentication_method,
        source=source,
        assurance=assurance,
        capabilities=capabilities,
    )
