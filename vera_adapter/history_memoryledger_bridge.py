"""Source-only bridge from authenticated ChatGPT graph evidence to MemoryLedger.

This module neither authenticates a user nor parses private messages. The host
must inject both an authenticated source resolver and a current authorizer.
Only bounded, historical-review proposals are emitted. No DMS record, model
context, semantic memory, or durable write is created.

MemoryLedger is an optional, unmerged source dependency. Import it only when a
trusted host deliberately invokes this bridge; ordinary Vera Adapter imports
remain independent of that candidate package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import math
import re
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from chatgpt_graph import HistoricalNode


_DIGEST = re.compile(r"[a-f0-9]{64}\Z")
_CLAIM_CEILING = "PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT"


@dataclass(frozen=True, repr=False)
class HostResolvedEvidence:
    """Private host assertion, NOT a self-authenticating credential.

    Source IDs are repeated to bind a resolver result to the exact input node.
    The host must independently prove source authentication, owner/speaker,
    privacy screening, speech-act classification and consent.
    """

    export_sha256: str
    conversation_id: str
    node_id: str
    tenant_id: str | None
    project_id: str | None
    identity_id: str | None
    privacy_scope: str | None
    occurred_at: datetime | None
    content_sha256: str | None
    speech_act: str | None
    owner_speaker_verified: bool = False
    third_party_screened_absent: bool = False
    corrects_event_id: str | None = None
    correction_link_verified: bool = False


@dataclass(frozen=True, repr=False)
class HistoricalReviewEnvelope:
    """In-memory pre-DMS candidate; intentionally has no memory_id/ledger_path."""

    event_id: str
    source_ref: str
    privacy_scope: str
    occurred_at: datetime
    disposition: str
    source_class: str = "CHATGPT_ACCOUNT_EXPORT_HISTORICAL"
    claim_ceiling: str = _CLAIM_CEILING


@dataclass(frozen=True, repr=False)
class BridgeDecision:
    disposition: str
    reason: str
    candidate: HistoricalReviewEnvelope | None = None
    claim_ceiling: str = _CLAIM_CEILING


def _hold(reason: str) -> BridgeDecision:
    return BridgeDecision("HOLD", reason)


def _source_instant(raw: object) -> datetime | None:
    """Interpret only explicitly recorded event time, never inferred time."""
    try:
        if type(raw) in (int, float) and math.isfinite(raw):
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        if type(raw) is str:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if value.tzinfo is not None and value.utcoffset() is not None:
                return value.astimezone(timezone.utc)
    except (OverflowError, OSError, ValueError):
        pass
    return None


def _private_refs(node: HistoricalNode, key: bytes) -> tuple[str, str, str]:
    # Length-delimit source IDs to avoid ambiguous concatenation. The HMAC
    # protects high-entropy source locators from casual public correlation.
    parts = (node.export_sha256, node.conversation_id, node.node_id)
    payload = "".join(f"{len(p)}:{p}" for p in parts).encode("utf-8")
    digest = hmac.new(key, payload, sha256).hexdigest()
    conv_parts = (node.export_sha256, node.conversation_id)
    conv_payload = "".join(f"{len(p)}:{p}" for p in conv_parts).encode("utf-8")
    conv_digest = hmac.new(key, conv_payload, sha256).hexdigest()
    return ("cg-" + digest[:48], "chatgpt:" + digest[16:64],
            "cgconv-" + conv_digest[:48])


def propose_historical_review(
    node: HistoricalNode,
    *,
    resolve_source: Callable[[HistoricalNode], HostResolvedEvidence | None],
    authorize: Callable[[object, datetime], object | None],
    private_locator_key: bytes,
    policy: object,
    at: datetime,
    index: object | None = None,
) -> BridgeDecision:
    """Ask the *real* MemoryLedger planner for a proposal, never an effect.

    The host is responsible for the trustworthiness of both callbacks, the
    completeness of a correction index, and private custody of all results.
    An imported archive never borrows STM's 30/45-day live-record expiry.
    """
    if not isinstance(private_locator_key, bytes) or len(private_locator_key) < 32:
        return _hold("PRIVATE_LOCATOR_KEY_REQUIRED")
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        return _hold("TRUSTED_AWARE_CLOCK_REQUIRED")
    if not callable(resolve_source) or not callable(authorize):
        return _hold("TRUSTED_HOST_CALLBACKS_REQUIRED")
    if not getattr(node, "has_message", False) or getattr(node, "role", None) != "user":
        return _hold("OWNER_USER_MESSAGE_REQUIRED")
    if not getattr(node, "message_id", None):
        return _hold("SOURCE_MESSAGE_ID_REQUIRED")
    if (not isinstance(getattr(node, "export_sha256", None), str)
            or not _DIGEST.fullmatch(node.export_sha256)
            or not isinstance(getattr(node, "conversation_id", None), str)
            or not node.conversation_id
            or not isinstance(getattr(node, "node_id", None), str)
            or not node.node_id):
        return _hold("INVALID_SOURCE_IDENTITY")
    try:
        bound = resolve_source(node)
    except Exception:
        return _hold("SOURCE_RESOLUTION_FAILED")
    if type(bound) is not HostResolvedEvidence:
        return _hold("AUTHENTICATED_SOURCE_BINDING_REQUIRED")
    if (bound.export_sha256 != node.export_sha256
            or bound.conversation_id != node.conversation_id
            or bound.node_id != node.node_id):
        return _hold("SOURCE_BINDING_MISMATCH")
    if (type(bound.owner_speaker_verified) is not bool
            or type(bound.third_party_screened_absent) is not bool
            or not bound.owner_speaker_verified
            or not bound.third_party_screened_absent):
        return _hold("SPEAKER_OR_PRIVACY_UNVERIFIED")
    if any(not isinstance(v, str) or not v for v in (
        bound.tenant_id, bound.project_id, bound.identity_id,
        bound.privacy_scope, bound.content_sha256,
    )) or not _DIGEST.fullmatch(bound.content_sha256):
        return _hold("MISSING_OR_INVALID_HOST_METADATA")
    recorded = _source_instant(node.event_time_raw)
    if recorded is None or bound.occurred_at is None:
        return _hold("EVENT_TIME_UNKNOWN")
    if (not isinstance(bound.occurred_at, datetime)
            or bound.occurred_at.tzinfo is None
            or bound.occurred_at.utcoffset() is None):
        return _hold("UNVERIFIED_EVENT_TIME")
    if abs((recorded - bound.occurred_at.astimezone(timezone.utc)).total_seconds()) > .001:
        return _hold("EVENT_TIME_SOURCE_MISMATCH")

    # This import is intentionally pinned to the advisory MemoryLedger
    # contract. Missing source dependency fails at this explicit seam.
    from memoryledger.contracts import (
        CandidateIndex, ConversationEvent, Disposition, HostAuthorization,
        LifecyclePolicy, Purpose, SpeechAct,
    )
    from memoryledger.planner import LifecyclePlanner

    if type(policy) is not LifecyclePolicy or policy.source_expiry_after is not None:
        return _hold("HISTORICAL_SOURCE_POLICY_REQUIRED")
    if policy.historical_review_after is None:
        return _hold("EXPLICIT_HISTORICAL_REVIEW_POLICY_REQUIRED")
    if bound.speech_act not in (SpeechAct.ASSERTION.value, SpeechAct.CORRECTION.value):
        return _hold("HISTORICAL_SPEECH_ACT_NOT_REVIEWABLE")
    if bound.speech_act == SpeechAct.CORRECTION.value and (
            not bound.correction_link_verified or not bound.corrects_event_id):
        return _hold("CORRECTION_ANCESTRY_UNVERIFIED")
    if bound.speech_act != SpeechAct.CORRECTION.value and bound.corrects_event_id:
        return _hold("INCONSISTENT_CORRECTION_CLASSIFICATION")

    event_id, source_ref, conversation_ref = _private_refs(node, private_locator_key)
    try:
        event = ConversationEvent(
            event_id=event_id, tenant_id=bound.tenant_id,
            project_id=bound.project_id, identity_id=bound.identity_id,
            conversation_id=conversation_ref, speaker="user",
            occurred_at=recorded, content_sha256=bound.content_sha256,
            source_ref=source_ref, privacy_scope=bound.privacy_scope,
            speech_act=SpeechAct(bound.speech_act),
            corrects_event_id=bound.corrects_event_id,
        )
        evidence_index = CandidateIndex() if index is None else index
        if type(evidence_index) is not CandidateIndex:
            return _hold("TRUSTED_CANDIDATE_INDEX_REQUIRED")
        try:
            grant = authorize(event, at)
        except Exception:
            grant = None
        if type(grant) is not HostAuthorization:
            return _hold("HOST_AUTHENTICATION_REQUIRED")
        if Purpose.CURRENT_REVIEW in grant.purposes:
            return _hold("CURRENT_REVIEW_FORBIDDEN_FOR_IMPORTED_HISTORY")
        if Purpose.HISTORICAL_REVIEW not in grant.purposes:
            return _hold("HISTORICAL_REVIEW_NOT_GRANTED")
        proposal = LifecyclePlanner(
            authorizer=lambda _event, _at: grant, policy=policy,
        ).propose(event, at=at, index=evidence_index)
    except (TypeError, ValueError):
        return _hold("INVALID_BRIDGE_CONTRACT")

    if proposal.disposition not in (
        Disposition.REVIEW_HISTORICAL, Disposition.REVIEW_CORRECTION,
    ):
        return _hold(proposal.reason)
    return BridgeDecision(
        proposal.disposition.value, proposal.reason,
        HistoricalReviewEnvelope(
            event_id=event.event_id, source_ref=event.source_ref,
            privacy_scope=event.privacy_scope, occurred_at=event.occurred_at,
            disposition=proposal.disposition.value,
        ),
    )
