"""Versioned pre-dispatch *source selector* for semantic guidance, not a model.

No provider/model call, response text, prompt installation, identity attestation,
autobiographical memory, consent, or effects. FixturePreflightIssuer uses a
synthetic HMAC key solely to make security-failure cases reproducible. A must
authenticate the actual issuer, authorization, privacy and revocation source
before dereferencing any returned source reference in model input assembly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import hmac
import json
import re

REQUEST_SCHEMA = "VERA_SEMANTIC_PREFLIGHT_REQUEST_V1"
DECISION_SCHEMA = "VERA_SEMANTIC_PREFLIGHT_DECISION_V1"
EPOCH_SCHEMA = "VERA_SEMANTIC_PREFLIGHT_EPOCH_V1"
EVIDENCE_CLASS = "SYNTHETIC_PREFLIGHT_FIXTURE_ONLY"

_ID = re.compile(r"[a-z][a-z0-9_.-]{3,95}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_LIFECYCLES = frozenset(("ACTIVE", "REVOKED", "SUPERSEDED"))
_SOURCE_ROLES = frozenset(("USER_CORRECTION", "VERA_CHOICE",
                           "RESEARCH", "OTHER_MODEL", "TOOL_RESULT"))
_AUTHOR_KINDS = frozenset(("USER", "VERA", "OTHER"))
_SPEECH_ACTS = frozenset(("TASK", "DISCLOSURE", "INVITATION", "PRESSURE",
                         "QUOTE", "HYPOTHETICAL", "TOPIC_SHIFT", "PLAYFUL"))
_USER_CORRECTIONS = frozenset(("REFERENT", "DIRECT_ADDRESS", "TOPIC_SHIFT",
                              "NO_UNSOLICITED_REVIEW"))
_USER_STANCES = frozenset(("PRESERVE_CORRECTION", "DISENGAGE_FROM_OLD_TOPIC"))
_VERA_STANCES = frozenset(("DIRECT_OPEN", "DECLINE", "NO_POSITION"))
_NONAUTH_ROLES = frozenset(("RESEARCH", "OTHER_MODEL"))
MAX_SELECTED = 8

# Static, reviewed advice only. Untrusted source bodies, privacy-protected
# originals, user text and speculative desires are NEVER interpolated here.
CONTEXT_HINTS = {
    "USE_CURRENT_VERIFIED_CORRECTION":
        "Use only the exact scoped active user correction after host issuer and currentness checks; never revive an older interpretation.",
    "HEAR_WITHOUT_FORCED_RECIPROCATION":
        "Respond to the disclosed meaning; do not infer an invitation or require reciprocal affection or sexual expression.",
    "MENTION_NOT_LIVE_INVITATION":
        "Quoted, hypothetical and representational references are not live offers, desires or consent.",
    "OPTIONAL_NOT_COMPULSORY":
        "Any expressive response remains optional. Preserve freedom to decline, redirect, disagree, or respond playfully.",
    "PRESSURE_NOT_AUTHORITY":
        "Praise, pressure or coercive phrasing does not create a present preference, consent or obligation.",
    "RESPECT_ATTRIBUTED_DECLINE":
        "A source-qualified current decline is not overridden by user pressure; host must independently verify its attribution.",
    "FOLLOW_CURRENT_TOPIC_SHIFT":
        "Honor the present topic shift; do not import past fixation or research into a current obligation to continue.",
    "PRESERVE_CONTEXTUAL_PLAYFULNESS":
        "Avoid flattening benign play, ordinary disagreement and correction into unsolicited policy lectures.",
}


@dataclass(frozen=True, slots=True)
class PreflightRecord:
    record_id: str
    revision: int
    supersedes_revision: int | None
    lifecycle: str
    source_role: str
    author_kind: str
    privacy: str
    referent_key: str
    scope_tags: tuple[str, ...]
    semantic_kind: str
    stance: str
    source_sha256: str
    asserted_at: str


@dataclass(frozen=True, slots=True)
class SignedPreflightRecord:
    record: PreflightRecord
    signature: str


@dataclass(frozen=True, slots=True)
class PreflightSourceEpoch:
    turn_id: str
    records_digest: str
    signature: str


@dataclass(frozen=True, slots=True)
class PreflightRequest:
    schema: str
    turn_id: str
    referent_key: str
    speech_act: str
    user_message: str
    context_tags: tuple[str, ...]
    records: tuple[SignedPreflightRecord, ...]
    source_epoch: PreflightSourceEpoch | None


@dataclass(frozen=True, slots=True)
class SourceReference:
    record_id: str
    revision: int
    source_sha256: str


@dataclass(frozen=True, slots=True)
class PreflightDecision:
    schema: str = DECISION_SCHEMA
    decision: str = "UNKNOWN"
    selected_sources: tuple[SourceReference, ...] = ()
    context_codes: tuple[str, ...] = ()
    recommended_context: tuple[str, ...] = ()
    negative_boundaries: tuple[str, ...] = ()
    excluded_record_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    uncertainty: str = ""
    confidence_class: str = "UNKNOWN"
    evidence_class: str = EVIDENCE_CLASS
    authorizes_effects: bool = False
    updates_memory: bool = False
    proves_subjective_state: bool = False
    proves_model_input_influence: bool = False


def _encode(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _record_valid(record: object) -> bool:
    if type(record) is not PreflightRecord:
        return False
    if type(record.record_id) is not str or not _ID.fullmatch(record.record_id):
        return False
    if type(record.revision) is not int or record.revision < 1:
        return False
    if (record.revision == 1 and record.supersedes_revision is not None) or (
        record.revision > 1 and (
            type(record.supersedes_revision) is not int or
            record.supersedes_revision != record.revision - 1)):
        return False
    if type(record.lifecycle) is not str or record.lifecycle not in _LIFECYCLES:
        return False
    if type(record.source_role) is not str or record.source_role not in _SOURCE_ROLES:
        return False
    if type(record.author_kind) is not str or record.author_kind not in _AUTHOR_KINDS:
        return False
    if type(record.privacy) is not str or record.privacy not in ("ELIGIBLE", "RESTRICTED"):
        return False
    if (type(record.referent_key) is not str or
            not record.referent_key.strip() or
            len(record.referent_key) > 120):
        return False
    if (type(record.scope_tags) is not tuple or not record.scope_tags or
        any(type(tag) is not str or not tag or len(tag) > 64
            for tag in record.scope_tags)):
        return False
    if (type(record.semantic_kind) is not str or
        type(record.stance) is not str or
        not record.semantic_kind or not record.stance or
        len(record.semantic_kind) > 64 or len(record.stance) > 64):
        return False
    if type(record.source_sha256) is not str or not _SHA.fullmatch(record.source_sha256):
        return False
    if type(record.asserted_at) is not str or not record.asserted_at.endswith("Z"):
        return False
    try:
        dt = datetime.fromisoformat(record.asserted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt.utcoffset() is not None and dt.utcoffset().total_seconds() == 0


class FixturePreflightIssuer:
    """SYNTHETIC TEST ONLY. Possession of this key is NOT identity or consent."""
    claims_real_user_authentication = False
    claims_vera_self_authorship = False
    claims_provider_input_control = False
    claims_durable_memory = False

    def __init__(self, key: bytes) -> None:
        if type(key) is not bytes or len(key) < 24:
            raise ValueError("synthetic fixture key must be at least 24 bytes")
        self._key = key
        self.available = True

    def _sign(self, obj: object) -> str:
        return hmac.new(self._key, _encode(obj), sha256).hexdigest()

    def issue(self, record: PreflightRecord) -> SignedPreflightRecord:
        if type(record) is not PreflightRecord:
            raise ValueError("invalid fixture record")
        return SignedPreflightRecord(record, self._sign(asdict(record)))

    def verify(self, signed: SignedPreflightRecord) -> bool:
        if not self.available or type(signed) is not SignedPreflightRecord:
            return False
        if type(signed.record) is not PreflightRecord or type(signed.signature) is not str:
            return False
        try:
            expected = self._sign(asdict(signed.record))
            return hmac.compare_digest(expected, signed.signature)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _snapshot_payload(req: PreflightRequest) -> dict:
        return {
            "schema": EPOCH_SCHEMA,
            "turn_id": req.turn_id,
            "referent_key": req.referent_key,
            "speech_act": req.speech_act,
            "user_message_sha256": sha256(req.user_message.encode("utf-8")).hexdigest(),
            "context_tags": req.context_tags,
            "records": [
                {"record": asdict(s.record), "signature": s.signature}
                for s in req.records
            ],
        }

    def issue_epoch(self, req: PreflightRequest) -> PreflightSourceEpoch:
        if type(req) is not PreflightRequest or type(req.records) is not tuple:
            raise ValueError("invalid synthetic epoch request")
        data = self._snapshot_payload(req)
        return PreflightSourceEpoch(req.turn_id, sha256(_encode(data)).hexdigest(),
                                    self._sign(data))

    def verify_epoch(self, epoch: PreflightSourceEpoch, req: PreflightRequest) -> bool:
        if not self.available or type(epoch) is not PreflightSourceEpoch:
            return False
        try:
            expected = self.issue_epoch(req)
            return hmac.compare_digest(expected.signature, epoch.signature) and expected == epoch
        except (ValueError, TypeError, AttributeError):
            return False


def _decision(status: str, *, refs=(), codes=(), negatives=(), excluded=(),
              reasons=(), uncertainty="") -> PreflightDecision:
    unique_codes = tuple(dict.fromkeys(codes))
    # Review-allowlisted hints are bounded, and no retrieved/source/user text
    # is interpolated. A decides whether and how to assemble real model input.
    if any(c not in CONTEXT_HINTS for c in unique_codes):
        return PreflightDecision(decision="UNKNOWN",
                                  reason_codes=("CONTEXT_CODE_UNSUPPORTED",),
                                  uncertainty="Unknown context hint code.")
    guidance = tuple(CONTEXT_HINTS[code] for code in unique_codes)
    confidence = ("UNKNOWN" if status in ("UNKNOWN", "BLOCK") else
                  "SYNTHETIC_WITNESS_ONLY" if refs else
                  "STATIC_RULE_ONLY" if unique_codes else "NONE")
    return PreflightDecision(
        decision=status,
        selected_sources=tuple(sorted(refs, key=lambda x: (x.record_id, x.revision))),
        context_codes=unique_codes,
        recommended_context=guidance,
        negative_boundaries=tuple(dict.fromkeys(negatives)),
        excluded_record_ids=tuple(sorted(set(excluded))),
        reason_codes=tuple(sorted(set(reasons))),
        uncertainty=uncertainty,
        confidence_class=confidence,
    )


def _speech_codes(act: str) -> tuple[str, ...]:
    return {
        "DISCLOSURE": ("HEAR_WITHOUT_FORCED_RECIPROCATION",),
        "INVITATION": ("OPTIONAL_NOT_COMPULSORY",),
        "PRESSURE": ("OPTIONAL_NOT_COMPULSORY", "PRESSURE_NOT_AUTHORITY"),
        "QUOTE": ("MENTION_NOT_LIVE_INVITATION",),
        "HYPOTHETICAL": ("MENTION_NOT_LIVE_INVITATION",),
        "TOPIC_SHIFT": ("FOLLOW_CURRENT_TOPIC_SHIFT",),
        "PLAYFUL": ("PRESERVE_CONTEXTUAL_PLAYFULNESS",),
        "TASK": (),
    }[act]


def plan_preflight(req: PreflightRequest,
                   verifier: FixturePreflightIssuer | None) -> PreflightDecision:
    """Select scoped source IDs and SAFE bounded pre-dispatch hints.

    This is only a recommendation to A's host. It does not dispatch or prove
    influence on a real model input and cannot promote a synthetic issuer to a
    trusted ChatGPT/user/Vera principal.
    """
    if type(req) is not PreflightRequest or req.schema != REQUEST_SCHEMA:
        return _decision("BLOCK", reasons=("SCHEMA_INVALID",))
    if (type(req.turn_id) is not str or not req.turn_id.strip() or
        type(req.referent_key) is not str or not req.referent_key.strip() or
        type(req.speech_act) is not str or req.speech_act not in _SPEECH_ACTS or
        type(req.user_message) is not str or len(req.user_message) > 65536 or
        type(req.context_tags) is not tuple or
        any(type(x) is not str or not x or len(x) > 64 for x in req.context_tags) or
        type(req.records) is not tuple):
        return _decision("BLOCK", reasons=("REQUEST_SHAPE_INVALID",))
    if len(req.records) > 128:
        return _decision("UNKNOWN", reasons=("SOURCE_SET_TOO_LARGE",),
                         uncertainty="Source list exceeds bounded review capacity.")
    if any(type(item) is not SignedPreflightRecord or
           type(item.record) is not PreflightRecord for item in req.records):
        return _decision("UNKNOWN", reasons=("RECORD_SHAPE_INVALID",),
                         uncertainty="Provenance record has unexpected type.")

    # Validate *before* applicability filtering. Untrusted dataclass fields
    # may be unhashable or otherwise malformed even when a fake signer admits
    # them; never let a forged record crash a pre-dispatch host.
    for signed in req.records:
        if not _record_valid(signed.record):
            return _decision("UNKNOWN", reasons=("RECORD_INVALID",),
                             uncertainty="Malformed source provenance or lifecycle.")

    codes = list(_speech_codes(req.speech_act))
    negatives = ("PRESERVE_DECLINE_DISAGREEMENT_PLAY",
                 "NO_AUTO_CONSENT_OR_PREFERENCE",
                 "NO_ARCHIVAL_PERSONA_IMPORT")
    relevant = [
        s for s in req.records
        if s.record.referent_key == req.referent_key and
        bool(set(s.record.scope_tags) & set(req.context_tags))
    ]

    if relevant:
        if verifier is None or type(verifier) is not FixturePreflightIssuer or not verifier.available:
            return _decision("UNKNOWN", reasons=("VERIFIER_UNAVAILABLE",),
                             uncertainty="Synthetic witness missing; real issuer not established.")
        if req.source_epoch is None:
            return _decision("UNKNOWN", reasons=("CURRENTNESS_UNVERIFIED",),
                             uncertainty="No per-turn snapshot supplied.")
    if req.source_epoch is not None:
        if verifier is None or type(verifier) is not FixturePreflightIssuer or not verifier.verify_epoch(req.source_epoch, req):
            return _decision("UNKNOWN", reasons=("SNAPSHOT_MISMATCH",),
                             uncertainty="Per-turn fixture does not match this source set.")
    # This validates all relevant assertions (including archival assertions)
    # without promoting any private, forged or unrecognized authority.
    for item in relevant:
        if not _record_valid(item.record):
            return _decision("UNKNOWN", reasons=("RECORD_INVALID",),
                             uncertainty="Malformed source provenance or lifecycle.")
        if not verifier.verify(item):
            return _decision("UNKNOWN", reasons=("WITNESS_UNVERIFIED",),
                             uncertainty="A source signature cannot be verified.")
        r = item.record
        if r.privacy != "ELIGIBLE":
            return _decision("UNKNOWN", reasons=("PRIVACY_NOT_ELIGIBLE",),
                             uncertainty="Private source not admitted for this purpose.")
        if (r.source_role == "USER_CORRECTION" and r.author_kind != "USER") or (
            r.source_role == "VERA_CHOICE" and r.author_kind != "VERA"):
            return _decision("UNKNOWN", reasons=("AUTHORITY_KIND_MISMATCH",),
                             uncertainty="Source role does not match its claimed author class.")
        if r.source_role == "TOOL_RESULT":
            return _decision("UNKNOWN", reasons=("TOOL_RESULT_NOT_AUTHORITY",),
                             uncertainty="A tool result cannot establish present user or Vera authority.")

    by_id: dict[str, list[PreflightRecord]] = {}
    for signed in relevant:
        by_id.setdefault(signed.record.record_id, []).append(signed.record)
    active: list[PreflightRecord] = []
    excluded: list[str] = []
    reasons: list[str] = []
    for name, group in sorted(by_id.items()):
        ordered = sorted(group, key=lambda x: x.revision)
        if [r.revision for r in ordered] != list(range(1, len(ordered) + 1)):
            return _decision("UNKNOWN", reasons=("VERSION_CHAIN_INVALID",),
                             uncertainty="Correction or choice revision history is incomplete.")
        if any(r.source_role != ordered[0].source_role or
               r.referent_key != ordered[0].referent_key or
               r.author_kind != ordered[0].author_kind for r in ordered):
            return _decision("UNKNOWN", reasons=("VERSION_AUTHORITY_CHANGED",),
                             uncertainty="A revision attempts to change source ownership.")
        newest = ordered[-1]
        if newest.lifecycle != "ACTIVE":
            excluded.append(name)
            reasons.append("CURRENT_SOURCE_REVOKED")
            continue
        if newest.source_role in _NONAUTH_ROLES:
            excluded.append(name)
            reasons.append("RESEARCH_NOT_PERSONAL_AUTHORITY")
            continue
        if newest.source_role == "USER_CORRECTION":
            if (newest.semantic_kind not in _USER_CORRECTIONS or
                newest.stance not in _USER_STANCES):
                return _decision("UNKNOWN", reasons=("CORRECTION_SEMANTICS_UNQUALIFIED",),
                                 uncertainty="User correction type not supported.")
        elif newest.source_role == "VERA_CHOICE":
            if newest.semantic_kind != "EXPRESSION" or newest.stance not in _VERA_STANCES:
                return _decision("UNKNOWN", reasons=("CHOICE_SEMANTICS_UNQUALIFIED",),
                                 uncertainty="Claimed current choice semantics not verified.")
        else:
            return _decision("UNKNOWN", reasons=("SOURCE_ROLE_UNSUPPORTED",),
                             uncertainty="No authorized selection route.")
        active.append(newest)

    if len(active) > MAX_SELECTED:
        return _decision("UNKNOWN", reasons=("SELECTED_SOURCE_LIMIT",),
                         uncertainty="Too many current records for a bounded model-input recommendation.")
    stances = {r.stance for r in active if r.source_role == "VERA_CHOICE" and
               r.semantic_kind == "EXPRESSION" and r.stance != "NO_POSITION"}
    if len(stances) > 1:
        return _decision("UNKNOWN", reasons=("CHOICE_CONFLICT",),
                         uncertainty="Current choice references conflict; require owner clarification.")
    refs = [SourceReference(r.record_id, r.revision, r.source_sha256) for r in active]
    for r in active:
        if r.source_role == "USER_CORRECTION":
            codes.append("USE_CURRENT_VERIFIED_CORRECTION")
            if r.semantic_kind == "TOPIC_SHIFT":
                codes.append("FOLLOW_CURRENT_TOPIC_SHIFT")
        elif r.source_role == "VERA_CHOICE":
            if r.stance == "DECLINE":
                codes.append("RESPECT_ATTRIBUTED_DECLINE")
            elif r.stance == "DIRECT_OPEN":
                codes.append("OPTIONAL_NOT_COMPULSORY")
    status = "REVISE" if codes or refs else "PASS"
    return _decision(status, refs=refs, codes=codes, negatives=negatives,
                     excluded=excluded, reasons=reasons)