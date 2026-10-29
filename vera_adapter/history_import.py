"""Read-only quarantine for normalized, historical ChatGPT claim candidates.

This is deliberately NOT a ChatGPT ZIP parser, memory store, tagger, model
context injector, or authority service. Caller-provided claims and timestamps
remain untrusted historical data. Real authorization is checked separately by
the continuity gate, and even a positive result is only downstream eligibility.
"""

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Callable, Iterable
from urllib.parse import quote

from .continuity import AdmissionResult, ContinuityCandidate, Verifier, inspect_continuity_import


_SOURCE_CLASSES = {
    "user": "USER_SUPPLIED",
    "assistant": "MODEL_OUTPUT",
    "tool": "EXTERNAL_SOURCE",
}


@dataclass(frozen=True)
class HistoryEvidence:
    """A normalized candidate, not a confirmed fact or an instruction.

    ``record_id`` is a caller-allocated identity in this batch. Source identity
    is derived from an authenticated export fingerprint and original IDs.
    ``claim_key`` is an untrusted comparison hint supplied by upstream triage,
    not a semantic equivalence proof. ``correction_of`` is a claimed link.
    """

    record_id: str
    export_fingerprint: str
    conversation_id: str
    message_id: str
    role: str
    occurred_at: str | None
    claim_key: str | None
    claim_text: str
    correction_of: str | None = None


@dataclass(frozen=True)
class StagedHistoryClaim:
    evidence: HistoryEvidence
    scope: str
    source_ref: str
    provenance_class: str
    status: str
    flags: tuple[str, ...]


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _source_ref(evidence: HistoryEvidence) -> str:
    return ("chatgpt-export:" + evidence.export_fingerprint + ":" +
            quote(evidence.conversation_id, safe="") + ":" +
            quote(evidence.message_id, safe=""))


def _timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not _nonblank(value):
        raise ValueError("timestamp must be a timezone-aware ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include an offset")
    return parsed


def stage_history_claims(
    records: Iterable[HistoryEvidence], *, scope: str,
) -> tuple[StagedHistoryClaim, ...]:
    """Quarantine normalized historical candidates, preserving ambiguity.

    This is a pure in-memory operation. Ingestion never writes memories, tags,
    identity, tools or model weights. Duplicate source IDs and dangling/cross-
    export correction links are errors rather than silent deduplication.
    """
    if not _nonblank(scope):
        raise ValueError("nonblank trusted owner scope required")
    items = list(records)
    ids: dict[str, HistoryEvidence] = {}
    sources: set[str] = set()
    times: dict[str, datetime | None] = {}
    by_key: dict[str, list[HistoryEvidence]] = {}

    for e in items:
        if not isinstance(e, HistoryEvidence):
            raise TypeError("expected HistoryEvidence")
        if any(not _nonblank(v) for v in (
            e.record_id, e.conversation_id, e.message_id, e.claim_text,
        )):
            raise ValueError("missing attributable source identity or candidate text")
        if not isinstance(e.export_fingerprint, str) or not re.fullmatch(
            r"[0-9a-f]{64}", e.export_fingerprint,
        ):
            raise ValueError("invalid export fingerprint")
        if not isinstance(e.role, str) or e.role not in _SOURCE_CLASSES:
            raise ValueError("unrecognized historical author role")
        if e.claim_key is not None and not _nonblank(e.claim_key):
            raise ValueError("claim_key must be nonblank or absent")
        if e.correction_of is not None and not _nonblank(e.correction_of):
            raise ValueError("correction_of must be nonblank or absent")
        if e.record_id in ids:
            raise ValueError("duplicate record_id")
        src = _source_ref(e)
        if src in sources:
            raise ValueError("duplicate source reference")
        ids[e.record_id] = e
        sources.add(src)
        times[e.record_id] = _timestamp(e.occurred_at)
        if e.claim_key is not None:
            by_key.setdefault(e.claim_key, []).append(e)

    for e in items:
        if e.correction_of is None:
            continue
        target = ids.get(e.correction_of)
        if target is None or target.record_id == e.record_id:
            raise ValueError("unknown correction target or self-correction")
        if target.export_fingerprint != e.export_fingerprint:
            raise ValueError("cross-export correction reference")

    # A claimed correction chain must be acyclic. A chain of many records is
    # checked iteratively so an account-sized import cannot overflow recursion.
    complete: set[str] = set()
    for e in items:
        visited: set[str] = set()
        cursor: str | None = e.record_id
        while cursor is not None and cursor not in complete:
            if cursor in visited:
                raise ValueError("correction cycle")
            visited.add(cursor)
            cursor = ids[cursor].correction_of
        complete.update(visited)

    staged = []
    for e in items:
        flags = ["HISTORICAL_UNTRUSTED"]
        if times[e.record_id] is None:
            flags.append("TIMESTAMP_UNKNOWN")
        if e.correction_of is not None:
            flags.append("HISTORICAL_CORRECTION_UNVERIFIED")
            before = times[e.correction_of]
            after = times[e.record_id]
            if before is not None and after is not None and after < before:
                flags.append("CORRECTION_TIMESTAMP_ANOMALY")
            if ids[e.correction_of].role != e.role:
                flags.append("CROSS_ROLE_CORRECTION_UNVERIFIED")
        if e.claim_key is not None:
            cohort = by_key[e.claim_key]
            if len({peer.claim_text for peer in cohort}) > 1:
                flags.append("VALUE_VARIANTS_REVIEW")
                known = [times[peer.record_id] for peer in cohort
                         if times[peer.record_id] is not None]
                if (known and times[e.record_id] is not None
                        and times[e.record_id] < max(known)):
                    flags.append("OLDER_HISTORICAL_VARIANT")
        staged.append(StagedHistoryClaim(
            evidence=e,
            scope=scope,
            source_ref=_source_ref(e),
            provenance_class=_SOURCE_CLASSES[e.role],
            status="QUARANTINED",
            flags=tuple(flags),
        ))
    return tuple(staged)


def inspect_history_admission(
    staged: StagedHistoryClaim, verifier: Verifier | None = None,
) -> AdmissionResult:
    """Check *possible* semantic-memory eligibility; never perform a write.

    Historical corrections and ambiguous value variants require a separate
    governed resolution contract. Only a trusted host-supplied verifier can
    approve an otherwise unambiguous candidate for downstream review.
    """
    if not isinstance(staged, StagedHistoryClaim) or staged.status != "QUARANTINED":
        raise TypeError("expected quarantined StagedHistoryClaim")

    def reject(reason: str) -> AdmissionResult:
        return AdmissionResult(False, reason, staged.provenance_class)

    # Do not accept a fabricated staging wrapper as source identity. The
    # authenticated host must still enforce owner authorization separately.
    if (not isinstance(staged.evidence, HistoryEvidence)
            or not _nonblank(staged.scope)
            or staged.source_ref != _source_ref(staged.evidence)
            or staged.provenance_class != _SOURCE_CLASSES.get(staged.evidence.role)
            or "HISTORICAL_UNTRUSTED" not in staged.flags):
        return reject("INVALID_STAGING_PROVENANCE")
    if "HISTORICAL_CORRECTION_UNVERIFIED" in staged.flags:
        return reject("CORRECTION_REQUIRES_SEPARATE_CONTRACT")
    if "VALUE_VARIANTS_REVIEW" in staged.flags:
        return reject("UNRESOLVED_HISTORICAL_VARIANTS")
    candidate = ContinuityCandidate(
        record_id=staged.evidence.record_id,
        source_kind=staged.provenance_class,
        source_ref=staged.source_ref,
        source_actor=staged.evidence.role,
        scope=staged.scope,
        target_state="semantic_memory",
        content=staged.evidence.claim_text,
        claims_lived_experience=False,
    )
    return inspect_continuity_import(candidate, verifier)
