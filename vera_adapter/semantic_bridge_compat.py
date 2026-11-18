"""Engineer B: optional, source-only V1 compatibility with A's one-hint bridge.

This is a constrained projection of an already computed semantic review. It
does not attest review identity, callback honesty, correction admission, model
provenance, delivery or consent. A's independent host still owns every effect.
"""
from __future__ import annotations

from dataclasses import replace

from .semantic_correction import ReviewDecision, ReviewRequest, FixtureVerifier, review_candidate

MAX_A_HINT_BYTES=256
MAX_A_HINT_ITEMS=8
REASON_TOO_LARGE="BRIDGE_GUIDANCE_TOO_LARGE"


def _unknown(decision:ReviewDecision)->ReviewDecision:
    return replace(
        decision,
        decision="UNKNOWN",
        reason_codes=tuple(sorted(set((*decision.reason_codes,REASON_TOO_LARGE)))),
        revision_guidance=(),
        uncertainty="Revision advice cannot be represented without loss in the A V1 bridge.",
        authorizes_effects=False,
        updates_memory=False,
        proves_subjective_state=False,
    )


def normalize_for_engineer_a_v1(decision:ReviewDecision)->ReviewDecision:
    """Keep V1 review semantics; convert at most one bounded revision hint.

    Two applicable corrections can give two distinct suggestions. A V1's
    EngineerBReviewPort accepts one revision_hint at most; without this
    projection it turns a legitimate REVISE into UNKNOWN. Do not drop a
    correction silently, inject source text, or loosen A's safety checks.
    """
    if type(decision) is not ReviewDecision:
        raise TypeError("expected exact B ReviewDecision")
    if decision.decision!="REVISE":
        return decision
    hints=decision.revision_guidance
    if (type(hints) is not tuple or len(hints)>MAX_A_HINT_ITEMS
            or any(type(x) is not str or not x.strip() for x in hints)):
        return _unknown(decision)
    if not hints:
        return decision
    unique=tuple(sorted(set(s.strip() for s in hints)))
    if len(unique)==1:
        if len(unique[0].encode("utf-8"))<=MAX_A_HINT_BYTES:
            return replace(decision,revision_guidance=unique)
        return _unknown(decision)
    consolidated=" ".join(f"{i+1}) {suggestion}" for i,suggestion in enumerate(unique))
    if len(consolidated.encode("utf-8"))>MAX_A_HINT_BYTES:
        return _unknown(decision)
    return replace(decision,revision_guidance=(consolidated,))


def review_for_engineer_a_v1(req:ReviewRequest,
                             verifier:FixtureVerifier|None)->ReviewDecision:
    """One B V1 review plus a schema-compatible, deterministic projection."""
    return normalize_for_engineer_a_v1(review_candidate(req,verifier))