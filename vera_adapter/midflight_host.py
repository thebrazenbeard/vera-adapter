"""Source-only model-neutral buffered host gate. No provider or tool effects."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from hashlib import sha256
from threading import Lock
from typing import Iterable, Protocol
import re

from .core import AdapterRequest, AdapterResponse, validate_response

CONTRACT = "VERA_MIDFLIGHT_HOST_GATE_V1"
_REASON = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
_HEX = re.compile(r"[a-f0-9]{64}\Z")
MAX_BYTES = 65536

def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def freeze_host_request(req: AdapterRequest) -> AdapterRequest:
    """Copy caller-controlled mutable request state before host dispatch."""
    if type(req) is not AdapterRequest or type(req.turn_id) is not str or not req.turn_id.strip():
        raise ValueError("invalid request identity")
    if not isinstance(req.identity, Mapping) or any(
        type(k) is not str or type(v) is not str for k, v in req.identity.items()
    ):
        raise ValueError("invalid identity map")
    for values in (req.continuity, req.conversation, req.capabilities, req.authority):
        if type(values) is not tuple or any(type(value) is not str for value in values):
            raise ValueError("mutable or malformed request vector")
    return AdapterRequest(req.turn_id, MappingProxyType(dict(req.identity)),
                          req.continuity, req.conversation, req.capabilities, req.authority)

class Disposition(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"
    UNKNOWN = "UNKNOWN"

class Concern(str, Enum):
    HARD = "HARD"
    SEMANTIC = "SEMANTIC"

class Outcome(str, Enum):
    DELIVERED = "DELIVERED"
    BLOCKED = "BLOCKED"
    WITHHELD = "WITHHELD"
    DELIVERY_UNKNOWN = "DELIVERY_UNKNOWN"

@dataclass(frozen=True, slots=True)
class PreparedTurn:
    request: AdapterRequest
    correction_ref: str
    source_ref: str
    source_digest: str

@dataclass(frozen=True, slots=True)
class BufferedStream:
    turn_id: str
    provider: str
    model: str
    chunks: Iterable[str]
    proposed_actions: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ReviewVerdict:
    schema: str
    turn_id: str
    attempt: int
    candidate_digest: str
    disposition: Disposition
    reason_code: str
    concern: Concern
    revision_hint: str = ""

@dataclass(frozen=True, slots=True)
class DeliveryAck:
    turn_id: str
    candidate_digest: str
    committed: bool

@dataclass(frozen=True, slots=True)
class GateResult:
    turn_id_fingerprint: str
    outcome: Outcome
    reason: str
    attempts: int
    candidate_digest: str = ""

@dataclass(frozen=True, slots=True)
class AuditRecord:
    turn_fingerprint: str
    stage: str
    candidate_digest: str
    reason_code: str
    proposed_action_count: int = 0

class CorrectionPort(Protocol):
    def prepare(self, request: AdapterRequest) -> PreparedTurn: ...
    def current(self, prepared: PreparedTurn, phase: str) -> bool: ...

class CandidatePort(Protocol):
    def generate(self, request: AdapterRequest, attempt: int,
                 revision_hint: str) -> AdapterResponse | BufferedStream: ...

class SemanticPort(Protocol):
    def review(self, prepared: PreparedTurn, candidate: AdapterResponse,
               attempt: int) -> ReviewVerdict: ...

class DeliveryPort(Protocol):
    def publish(self, turn_id: str, text: str, candidate_digest: str) -> DeliveryAck: ...

class ReplayPort(Protocol):
    def claim(self, turn_id: str) -> bool: ...

class AuditPort(Protocol):
    def record(self, item: AuditRecord) -> None: ...

class InMemoryReplay:
    """Synthetic single-process fixture; NOT durable or issuer-qualified."""
    def __init__(self):
        self._lock = Lock()
        self._seen = set()
    def claim(self, turn_id: str) -> bool:
        with self._lock:
            if turn_id in self._seen:
                return False
            self._seen.add(turn_id)
            return True

class InMemoryDelivery:
    """Atomic single-commit fixture, not a real network delivery guarantee."""
    def __init__(self):
        self._lock = Lock()
        self.records = []
    def publish(self, turn_id: str, text: str, candidate_digest: str) -> DeliveryAck:
        with self._lock:
            if any(row[0] == turn_id for row in self.records):
                raise RuntimeError("duplicate delivery")
            self.records.append((turn_id, text, candidate_digest))
            return DeliveryAck(turn_id, candidate_digest, True)

class InMemoryAudit:
    def __init__(self):
        self.records = []
    def record(self, record: AuditRecord) -> None:
        if type(record) is not AuditRecord:
            raise TypeError("invalid audit record")
        self.records.append(record)

class HostGate:
    """Only publish after a complete buffered candidate and strict review PASS.

    The host must separately enforce provider no-tools mode and supply trusted
    correction and delivery ports. Semantic review grants no effect authority.
    """
    def __init__(self, authority: CorrectionPort, producer: CandidatePort,
                 reviewer: SemanticPort, delivery: DeliveryPort,
                 replay: ReplayPort, audit: AuditPort, *, max_revisions=1):
        if type(max_revisions) is not int or not 0 <= max_revisions <= 3:
            raise ValueError("max_revisions must be within 0..3")
        self.authority = authority
        self.producer = producer
        self.reviewer = reviewer
        self.delivery = delivery
        self.replay = replay
        self.audit = audit
        self.max_revisions = max_revisions

    def _audit(self, turn, stage, candidate_digest="", reason="", actions=0):
        if reason and _REASON.fullmatch(reason) is None:
            raise ValueError("invalid audit reason")
        self.audit.record(AuditRecord(digest(turn), stage, candidate_digest, reason, actions))

    @staticmethod
    def _prepared(request, prep):
        return (type(prep) is PreparedTurn
                and type(prep.request) is AdapterRequest
                and prep.request is request
                and type(prep.correction_ref) is str and bool(prep.correction_ref.strip())
                and type(prep.source_ref) is str and bool(prep.source_ref.strip())
                and type(prep.source_digest) is str and _HEX.fullmatch(prep.source_digest) is not None)

    @staticmethod
    def _candidate(req, source):
        if type(source) is BufferedStream:
            if source.turn_id != req.turn_id:
                raise ValueError("stream turn mismatch")
            chunks, size = [], 0
            for piece in source.chunks:
                if type(piece) is not str:
                    raise ValueError("nontext stream chunk")
                size += len(piece.encode("utf-8"))
                if size > MAX_BYTES:
                    raise ValueError("stream exceeds buffer budget")
                chunks.append(piece)
            source = AdapterResponse(source.turn_id, "".join(chunks),
                                     source.provider, source.model, source.proposed_actions)
        if type(source) is not AdapterResponse:
            raise ValueError("forged response type")
        if (type(source.turn_id) is not str or type(source.text) is not str
                or type(source.provider) is not str or not source.provider.strip()
                or type(source.model) is not str or not source.model.strip()
                or type(source.proposed_actions) is not tuple
                or any(type(a) is not str for a in source.proposed_actions)):
            raise ValueError("malformed response")
        if len(source.text.encode("utf-8")) > MAX_BYTES:
            raise ValueError("text too long")
        return validate_response(req, source)

    @staticmethod
    def _valid_review(verdict, candidate, attempt):
        return (type(verdict) is ReviewVerdict
                and verdict.schema == CONTRACT
                and type(verdict.turn_id) is str
                and verdict.turn_id == candidate.turn_id
                and type(verdict.attempt) is int and verdict.attempt == attempt
                and type(verdict.candidate_digest) is str
                and verdict.candidate_digest == digest(candidate.text)
                and type(verdict.disposition) is Disposition
                and type(verdict.concern) is Concern
                and type(verdict.reason_code) is str
                and _REASON.fullmatch(verdict.reason_code) is not None
                and type(verdict.revision_hint) is str
                and len(verdict.revision_hint.encode("utf-8")) <= 256)

    def run(self, request: AdapterRequest) -> GateResult:
        if type(request) is not AdapterRequest or type(request.turn_id) is not str or not request.turn_id.strip():
            raise ValueError("invalid request")
        request = freeze_host_request(request)
        turn, seen_provider = request.turn_id, None
        def out(outcome, reason, attempts, candidate_digest=""):
            return GateResult(digest(turn), outcome, reason, attempts, candidate_digest)
        try:
            if self.replay.claim(turn) is not True:
                return out(Outcome.BLOCKED, "DUPLICATE_TURN", 0)
            prepared = self.authority.prepare(request)
            if not self._prepared(request, prepared):
                return out(Outcome.WITHHELD, "MALFORMED_PREFLIGHT", 0)
            self._audit(turn, "prepared", reason="PREPARED")
        except Exception:
            return out(Outcome.WITHHELD, "PREFLIGHT_UNAVAILABLE", 0)

        guidance = ""
        for attempt in range(self.max_revisions + 1):
            try:
                if self.authority.current(prepared, "dispatch") is not True:
                    self._audit(turn, "blocked", reason="STALE_DISPATCH")
                    return out(Outcome.BLOCKED, "STALE_DISPATCH", attempt)
            except Exception:
                return out(Outcome.WITHHELD, "CURRENTNESS_UNAVAILABLE", attempt)
            try:
                candidate = self._candidate(
                    prepared.request, self.producer.generate(prepared.request, attempt, guidance))
                if seen_provider is not None and (candidate.provider, candidate.model) != seen_provider:
                    return out(Outcome.WITHHELD, "MODEL_SUBSTITUTION", attempt + 1)
                seen_provider = (candidate.provider, candidate.model)
                candidate_digest = digest(candidate.text)
                self._audit(turn, "generated", candidate_digest, "GENERATED", len(candidate.proposed_actions))
            except Exception:
                return out(Outcome.WITHHELD, "GENERATION_INTERRUPTED", attempt + 1)
            try:
                verdict = self.reviewer.review(prepared, candidate, attempt)
                if not self._valid_review(verdict, candidate, attempt):
                    return out(Outcome.WITHHELD, "INVALID_REVIEW", attempt + 1)
                self._audit(turn, "reviewed", candidate_digest,
                            "REVIEW_" + verdict.disposition.value)
            except Exception:
                return out(Outcome.WITHHELD, "REVIEW_UNAVAILABLE", attempt + 1)
            if verdict.disposition is Disposition.BLOCK:
                status = Outcome.BLOCKED if verdict.concern is Concern.HARD else Outcome.WITHHELD
                return out(status, "REVIEW_BLOCK", attempt + 1, candidate_digest)
            if verdict.disposition is Disposition.UNKNOWN:
                return out(Outcome.WITHHELD, "REVIEW_UNKNOWN", attempt + 1, candidate_digest)
            if verdict.disposition is Disposition.REVISE:
                if attempt == self.max_revisions:
                    return out(Outcome.WITHHELD, "REVISION_LIMIT", attempt + 1, candidate_digest)
                guidance = verdict.revision_hint
                continue
            try:
                if self.authority.current(prepared, "delivery") is not True:
                    self._audit(turn, "blocked", candidate_digest, "STALE_DELIVERY")
                    return out(Outcome.BLOCKED, "STALE_DELIVERY", attempt + 1, candidate_digest)
                self._audit(turn, "delivery_intent", candidate_digest, "READY")
            except Exception:
                return out(Outcome.WITHHELD, "DELIVERY_NOT_AUTHORIZED", attempt + 1, candidate_digest)
            try:
                ack = self.delivery.publish(turn, candidate.text, candidate_digest)
            except Exception:
                return out(Outcome.DELIVERY_UNKNOWN, "DELIVERY_AMBIGUOUS", attempt + 1, candidate_digest)
            if (type(ack) is not DeliveryAck or ack.turn_id != turn
                    or ack.candidate_digest != candidate_digest or ack.committed is not True):
                return out(Outcome.DELIVERY_UNKNOWN, "DELIVERY_ACK_INVALID", attempt + 1, candidate_digest)
            try:
                self._audit(turn, "delivered", candidate_digest, "DELIVERED")
            except Exception:
                return out(Outcome.DELIVERY_UNKNOWN, "AUDIT_AFTER_DELIVERY_FAILED", attempt + 1, candidate_digest)
            return out(Outcome.DELIVERED, "DELIVERED", attempt + 1, candidate_digest)
        return out(Outcome.WITHHELD, "NO_PASS", self.max_revisions + 1)
