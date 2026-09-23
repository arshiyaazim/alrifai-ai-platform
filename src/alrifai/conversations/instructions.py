"""C5 versioned Admin/Owner conversation instructions and selection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4

from ..authorization import AuthorizationDenied, Capability, PrincipalType, TrustedPrincipal, require_capability


class InstructionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class InstructionEventType(StrEnum):
    CREATED = "created"
    ACTIVATED = "activated"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class InstructionError(ValueError):
    pass


class InstructionConflictError(RuntimeError):
    def __init__(self, evidence: tuple["SelectionEvidence", ...]):
        super().__init__("unresolved same-authority instruction conflict")
        self.evidence = evidence


@dataclass(frozen=True)
class InstructionScope:
    domain: str | None = None
    topic_id: UUID | None = None
    conversation_id: UUID | None = None
    role: str | None = None
    audience: str | None = None
    channel: str | None = None
    source_account: str | None = None

    def __post_init__(self):
        for name in ("domain", "role", "audience", "channel", "source_account"):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise InstructionError(f"{name} scope must not be blank")

    @property
    def specificity(self) -> int:
        return sum(value is not None for value in (
            self.domain, self.topic_id, self.conversation_id, self.role,
            self.audience, self.channel, self.source_account,
        ))


@dataclass(frozen=True)
class InstructionDraft:
    subject_key: str
    content: str
    scope: InstructionScope = field(default_factory=InstructionScope)
    priority: int = 0
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    instruction_id: UUID | None = None
    supersedes_version_id: UUID | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    provenance: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.subject_key.strip() or not self.content.strip():
            raise InstructionError("subject_key and content are required")
        _aware(self.effective_from, "effective_from")
        if self.expires_at is not None:
            _aware(self.expires_at, "expires_at")
            if self.expires_at <= self.effective_from:
                raise InstructionError("expires_at must follow effective_from")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise InstructionError("idempotency_key must not be blank")
        if self.idempotency_key is None:
            raise InstructionError("idempotency_key is required")
        if self.scope.topic_id is not None and self.scope.conversation_id is None:
            raise InstructionError("topic scope requires its canonical conversation ID")
        if not isinstance(self.provenance, tuple) or any(not value.strip() for value in self.provenance):
            raise InstructionError("provenance must be a tuple of non-blank references")


@dataclass(frozen=True)
class InstructionVersion:
    version_id: UUID
    instruction_id: UUID
    version: int
    subject_key: str
    content: str
    issuer_type: PrincipalType
    issuer_principal_id: UUID
    scope: InstructionScope
    priority: int
    effective_from: datetime
    expires_at: datetime | None
    supersedes_version_id: UUID | None
    created_at: datetime
    correlation_id: str | None
    idempotency_key: str | None
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class InstructionEvent:
    version_id: UUID
    event_type: InstructionEventType
    actor_principal_id: UUID
    occurred_at: datetime
    idempotency_key: str | None
    correlation_id: str | None
    reason: str | None = None


@dataclass(frozen=True)
class InstructionContext:
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    domain: str | None = None
    topic_id: UUID | None = None
    topic_state: str | None = None
    conversation_id: UUID | None = None
    role: str | None = None
    audience: str | None = None
    channel: str | None = None
    source_account: str | None = None

    def __post_init__(self):
        _aware(self.at, "selection time")


@dataclass(frozen=True)
class SelectionEvidence:
    version_id: UUID
    included: bool
    reason: str


@dataclass(frozen=True)
class InstructionSelection:
    selected: tuple[InstructionVersion, ...]
    evidence: tuple[SelectionEvidence, ...]


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InstructionError(f"{name} must include a timezone")


def _trusted_manager(value: object) -> TrustedPrincipal:
    if not isinstance(value, TrustedPrincipal) or value.principal_type not in {
        PrincipalType.OWNER, PrincipalType.ADMIN,
    }:
        raise AuthorizationDenied("trusted Owner or Admin principal required")
    require_capability(value, Capability.MANAGE_CONVERSATIONS)
    return value


def _status(events: tuple[InstructionEvent, ...], at: datetime | None = None) -> InstructionStatus:
    kinds = {event.event_type for event in events if at is None or event.occurred_at <= at}
    if InstructionEventType.REVOKED in kinds:
        return InstructionStatus.REVOKED
    if InstructionEventType.SUPERSEDED in kinds:
        return InstructionStatus.SUPERSEDED
    return InstructionStatus.ACTIVE if InstructionEventType.ACTIVATED in kinds else InstructionStatus.DRAFT


class InMemoryInstructionStore:
    """Thread-safe ephemeral store for unit tests."""

    def __init__(self):
        self.versions: dict[UUID, InstructionVersion] = {}
        self.history: dict[UUID, list[InstructionEvent]] = {}
        self._lock = RLock()

    def create(self, version, event):
        with self._lock:
            for old in self.versions.values():
                if version.idempotency_key and (old.issuer_principal_id, old.idempotency_key) == (
                    version.issuer_principal_id, version.idempotency_key
                ):
                    if not _same_instruction(old, version):
                        raise InstructionError("idempotency key reused with different instruction data")
                    return old
            self.versions[version.version_id] = version
            self.history[version.version_id] = [event]
            return version

    def get(self, version_id):
        return self.versions.get(version_id)

    def all(self):
        return tuple(self.versions.values())

    def events(self, version_id):
        return tuple(self.history.get(version_id, ()))

    def append(self, event):
        with self._lock:
            history = self.history.get(event.version_id)
            if history is None:
                raise InstructionError("instruction version not found")
            old = next((e for versions in self.history.values() for e in versions
                        if event.idempotency_key and e.actor_principal_id == event.actor_principal_id
                        and e.idempotency_key == event.idempotency_key), None)
            if old and (old.version_id, old.event_type) != (event.version_id, event.event_type):
                raise InstructionError("idempotency key reused for a different lifecycle event")
            old = old or next((e for e in history if e.event_type is event.event_type), None)
            if old:
                return old
            history.append(event)
            return event


class PostgresInstructionStore:
    """DB-API adapter for immutable V009 version rows and append-only events."""

    def __init__(self, connection):
        self.connection = connection

    def create(self, version, event):
        try:
            row = self._one("""INSERT INTO conversation_ai_instruction_versions
                (version_id,instruction_id,version,subject_key,content,issuer_type,issuer_principal_id,
                 scope,conversation_scope_id,topic_scope_id,priority,effective_from,expires_at,
                 supersedes_version_id,created_at,correlation_id,idempotency_key,provenance)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                ON CONFLICT (issuer_principal_id,idempotency_key) DO NOTHING RETURNING version_id""",
                _version_params(version))
            if row is None:
                old = self._one("SELECT version_id FROM conversation_ai_instruction_versions "
                                "WHERE issuer_principal_id=%s AND idempotency_key=%s",
                                (version.issuer_principal_id, version.idempotency_key))
                existing = self.get(UUID(str(old[0]))) if old else None
                if not existing or not _same_instruction(existing, version):
                    raise InstructionError("idempotency key reused with different instruction data")
                self.connection.commit()
                return existing
            if self._persist_event(event):
                self._audit(version.version_id, "CREATE", event)
            self.connection.commit()
            return version
        except Exception:
            self.connection.rollback()
            raise

    def get(self, version_id):
        row = self._one("SELECT * FROM conversation_ai_instruction_versions WHERE version_id=%s", (version_id,))
        return _version_from_row(row) if row else None

    def all(self):
        return tuple(_version_from_row(row) for row in self._all(
            "SELECT * FROM conversation_ai_instruction_versions ORDER BY created_at,version_id"))

    def events(self, version_id):
        rows = self._all("""SELECT version_id,event_type,actor_principal_id,occurred_at,
            idempotency_key,correlation_id,reason FROM conversation_ai_instruction_events
            WHERE version_id=%s ORDER BY occurred_at,event_id""", (version_id,))
        return tuple(_event_from_row(row) for row in rows)

    def append(self, event):
        try:
            old = self._one("""SELECT version_id,event_type,actor_principal_id,occurred_at,
                idempotency_key,correlation_id,reason FROM conversation_ai_instruction_events
                WHERE version_id=%s AND event_type=%s""", (event.version_id, event.event_type.value))
            if old:
                self.connection.commit()
                return _event_from_row(old)
            inserted = self._persist_event(event)
            if inserted:
                self._audit(event.version_id, "UPDATE", event)
            self.connection.commit()
            return event
        except Exception:
            self.connection.rollback()
            raise

    def activate(self, event, superseded):
        try:
            if self._persist_event(event):
                self._audit(event.version_id, "UPDATE", event)
            if superseded and self._persist_event(superseded):
                self._audit(superseded.version_id, "UPDATE", superseded)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _insert_event(self, event):
        return self._one("""INSERT INTO conversation_ai_instruction_events
            (version_id,event_type,actor_principal_id,occurred_at,idempotency_key,correlation_id,reason)
            VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING event_id""",
            (event.version_id,event.event_type.value,event.actor_principal_id,event.occurred_at,
             event.idempotency_key,event.correlation_id,event.reason))

    def _persist_event(self, event):
        if event.idempotency_key:
            old = self._one("""SELECT version_id,event_type FROM conversation_ai_instruction_events
                WHERE actor_principal_id=%s AND idempotency_key=%s""",
                (event.actor_principal_id, event.idempotency_key))
            if old:
                if (UUID(str(old[0])), InstructionEventType(old[1])) != (event.version_id, event.event_type):
                    raise InstructionError("idempotency key reused for a different lifecycle event")
                return False
        if self._insert_event(event):
            return True
        old = self._one("""SELECT version_id,event_type FROM conversation_ai_instruction_events
            WHERE version_id=%s AND event_type=%s""", (event.version_id,event.event_type.value))
        if old and (UUID(str(old[0])), InstructionEventType(old[1])) == (event.version_id,event.event_type):
            return False
        raise InstructionError("lifecycle event conflicts with an existing idempotency key")

    def _audit(self, version_id, action, event):
        self._one("""INSERT INTO audit_log(entity_type,entity_id,action,actor_principal_id,
            after_state,correlation_id) VALUES (%s,%s,%s,%s,%s::jsonb,%s) RETURNING audit_id""",
            ("conversation_ai_instruction",version_id,action,event.actor_principal_id,
             json.dumps({"event":event.event_type.value,"reason":event.reason}),event.correlation_id))

    def _one(self, sql, params=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _all(self, sql, params=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()


class InstructionService:
    def __init__(self, store, *, clock=None):
        self.store = store
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self):
        value = self._clock()
        _aware(value, "clock")
        return value

    def create_version(self, principal, draft: InstructionDraft):
        actor = _trusted_manager(principal)
        prior = self.store.get(draft.supersedes_version_id) if draft.supersedes_version_id else None
        if draft.supersedes_version_id and prior is None:
            raise InstructionError("superseded version does not exist")
        if prior and prior.instruction_id != (draft.instruction_id or prior.instruction_id):
            raise InstructionError("a revision must retain its instruction ID")
        if prior and prior.issuer_type is PrincipalType.OWNER and actor.principal_type is not PrincipalType.OWNER:
            raise AuthorizationDenied("Admin cannot supersede an Owner instruction")
        instruction_id = draft.instruction_id or (prior.instruction_id if prior else uuid4())
        number = max((v.version for v in self.store.all() if v.instruction_id == instruction_id), default=0) + 1
        version = InstructionVersion(uuid4(), instruction_id, number, draft.subject_key.strip(),
            draft.content.strip(), actor.principal_type, actor.principal_id, draft.scope, draft.priority,
            draft.effective_from, draft.expires_at, draft.supersedes_version_id,
            self._now(), draft.correlation_id, draft.idempotency_key, draft.provenance)
        event = self._event(actor, version.version_id, InstructionEventType.CREATED,
                            draft.idempotency_key + ":created", draft.correlation_id)
        return self.store.create(version, event)

    def activate(self, principal, version_id, *, idempotency_key, correlation_id=None):
        actor = _trusted_manager(principal)
        _require_idempotency_key(idempotency_key)
        version = self._managed(actor, version_id)
        status = _status(self.store.events(version_id))
        if status is InstructionStatus.ACTIVE:
            return version
        if status is not InstructionStatus.DRAFT:
            raise InstructionError(f"cannot activate {status.value} instruction")
        old_event = None
        if version.supersedes_version_id:
            old = self._managed(actor, version.supersedes_version_id)
            if _status(self.store.events(old.version_id)) is InstructionStatus.ACTIVE:
                old_event = self._event(actor, old.version_id, InstructionEventType.SUPERSEDED,
                    idempotency_key + ":superseded", correlation_id, f"superseded_by:{version_id}",
                    version.effective_from)
        event = self._event(actor, version_id, InstructionEventType.ACTIVATED, idempotency_key, correlation_id)
        if hasattr(self.store, "activate"):
            self.store.activate(event, old_event)
        else:
            self.store.append(event)
            if old_event:
                self.store.append(old_event)
        return version

    def revoke(self, principal, version_id, *, idempotency_key, reason, correlation_id=None):
        actor = _trusted_manager(principal)
        _require_idempotency_key(idempotency_key)
        version = self._managed(actor, version_id)
        if not reason.strip():
            raise InstructionError("revocation reason is required")
        status = self.status(version_id)
        if status is InstructionStatus.SUPERSEDED:
            raise InstructionError("superseded instruction versions are immutable historical records")
        old = next((e for e in self.store.events(version_id)
                    if e.event_type is InstructionEventType.REVOKED), None)
        if old:
            return old
        return self.store.append(self._event(actor, version.version_id, InstructionEventType.REVOKED,
                                             idempotency_key, correlation_id, reason))

    def status(self, version_id):
        if self.store.get(version_id) is None:
            raise InstructionError("instruction version not found")
        return _status(self.store.events(version_id), self._now())

    def select(self, context: InstructionContext) -> InstructionSelection:
        eligible, evidence = [], []
        for version in self.store.all():
            status = _status(self.store.events(version.version_id), context.at)
            if status is not InstructionStatus.ACTIVE:
                reason = status.value.upper()
            elif context.at < version.effective_from:
                reason = "NOT_YET_EFFECTIVE"
            elif version.expires_at is not None and context.at >= version.expires_at:
                reason = "EXPIRED"
            elif not _scope_matches(version.scope, context):
                reason = "SCOPE_MISMATCH"
            elif version.scope.topic_id and context.topic_state in {"closed", "completed"}:
                reason = "TOPIC_CLOSED"
            else:
                reason = None
            if reason:
                evidence.append(SelectionEvidence(version.version_id, False, reason))
            else:
                eligible.append(version)
        selected, conflicts = [], []
        for subject in sorted({v.subject_key for v in eligible}):
            group = [v for v in eligible if v.subject_key == subject]
            owners = [v for v in group if v.issuer_type is PrincipalType.OWNER]
            admins = [v for v in group if v.issuer_type is PrincipalType.ADMIN]
            ow, ol = _ranked(owners)
            aw, al = _ranked(admins)
            if ow and aw and {v.content for v in ow} != {v.content for v in aw}:
                selected.extend(ow)
                evidence.extend(SelectionEvidence(v.version_id, False, "OWNER_PRECEDENCE_SAME_SUBJECT") for v in aw)
            else:
                selected.extend(ow + aw)
            evidence.extend(SelectionEvidence(v.version_id, False, "LOWER_CANONICAL_PRECEDENCE") for v in ol + al)
            if ow and aw and {v.content for v in ow} != {v.content for v in aw}:
                conflicts.extend(_rank_ties(owners))
            else:
                conflicts.extend(_rank_ties(owners) + _rank_ties(admins))
        if conflicts:
            evidence.extend(SelectionEvidence(v.version_id, False, "SAME_AUTHORITY_CONFLICT") for v in conflicts)
            raise InstructionConflictError(tuple(evidence))
        evidence.extend(SelectionEvidence(v.version_id, True, "APPLICABLE") for v in selected)
        selected.sort(key=lambda v: (v.subject_key, v.issuer_type.value, str(v.version_id)))
        return InstructionSelection(tuple(selected), tuple(evidence))

    def _managed(self, actor, version_id):
        version = self.store.get(version_id)
        if version is None:
            raise InstructionError("instruction version not found")
        if actor.principal_type is PrincipalType.ADMIN and version.issuer_type is PrincipalType.OWNER:
            raise AuthorizationDenied("Admin cannot change Owner instruction lifecycle")
        return version

    def _event(self, actor, version_id, event_type, key, correlation, reason=None, occurred_at=None):
        return InstructionEvent(version_id, event_type, actor.principal_id,
            occurred_at or self._now(), key, correlation, reason)


def _same_instruction(left, right):
    return (
        left.subject_key, left.content, left.issuer_type, left.scope, left.priority,
        left.effective_from, left.expires_at, left.supersedes_version_id, left.provenance,
    ) == (
        right.subject_key, right.content, right.issuer_type, right.scope, right.priority,
        right.effective_from, right.expires_at, right.supersedes_version_id, right.provenance,
    )


def _require_idempotency_key(key):
    if not isinstance(key, str) or not key.strip():
        raise InstructionError("idempotency_key is required")


def _scope_matches(scope, context):
    return all(getattr(scope, name) is None or getattr(scope, name) == getattr(context, name)
               for name in ("domain","topic_id","conversation_id","role","audience","channel","source_account"))


def _rank(version):
    return (version.scope.specificity, version.priority, version.effective_from, version.version)


def _ranked(versions):
    if not versions:
        return [], []
    best = max(_rank(v) for v in versions)
    return [v for v in versions if _rank(v) == best], [v for v in versions if _rank(v) != best]


def _rank_ties(versions):
    winners, _ = _ranked(versions)
    return winners if len(winners) > 1 and len({v.content for v in winners}) > 1 else []


def _version_params(v):
    scope = {name: value for name, value in (
        ("domain",v.scope.domain),("role",v.scope.role),
        ("audience",v.scope.audience),("channel",v.scope.channel),
        ("source_account",v.scope.source_account))}
    return (v.version_id,v.instruction_id,v.version,v.subject_key,v.content,v.issuer_type.value,
            v.issuer_principal_id,json.dumps(scope),v.scope.conversation_id,v.scope.topic_id,
            v.priority,v.effective_from,v.expires_at,
            v.supersedes_version_id,v.created_at,v.correlation_id,v.idempotency_key,json.dumps(v.provenance))


def _version_from_row(row):
    raw = row[7] if isinstance(row[7], dict) else json.loads(row[7])
    raw["conversation_id"] = UUID(str(row[8])) if row[8] else None
    raw["topic_id"] = UUID(str(row[9])) if row[9] else None
    scope = InstructionScope(**raw)
    provenance = row[17] if isinstance(row[17], list) else json.loads(row[17])
    return InstructionVersion(UUID(str(row[0])),UUID(str(row[1])),row[2],row[3],row[4],
        PrincipalType(row[5].lower()),UUID(str(row[6])),scope,row[10],row[11],row[12],
        UUID(str(row[13])) if row[13] else None,row[14],row[15],row[16],tuple(provenance))


def _event_from_row(row):
    return InstructionEvent(UUID(str(row[0])),InstructionEventType(row[1]),UUID(str(row[2])),
                            row[3],row[4],row[5],row[6])
