"""Engineer A adapter for Engineer B's unmerged semantic Decision V1.

The source of decisions remains B-owned and must be injected by a trusted host.
This class does not import B's source or forge an issuer/currentness claim.
"""
from __future__ import annotations
from collections.abc import Callable

from .core import AdapterResponse
from .midflight_host import (
    CONTRACT, Concern, Disposition, PreparedTurn, ReviewVerdict, digest,
)

B_REQUEST = "VERA_SEMANTIC_REVIEW_REQUEST_V1"
B_DECISION = "VERA_SEMANTIC_REVIEW_DECISION_V1"
B_EVIDENCE = "SYNTHETIC_EVALUATION_ONLY"


class EngineerBReviewPort:
    """Structural, fail-unknown translation, NOT authentication of B's callback.

    An independently authorized host owns the request builder, currentness and
    callback. B outputs cannot authorize host effects, memory or delivery.
    """
    def __init__(self, build_subject: Callable, evaluate: Callable):
        self._build = build_subject
        self._evaluate = evaluate

    def review(self, prepared: PreparedTurn, candidate: AdapterResponse,
               attempt: int) -> ReviewVerdict:
        turn_id = candidate.turn_id
        candidate_digest = digest(candidate.text)

        def unknown() -> ReviewVerdict:
            return ReviewVerdict(
                CONTRACT, turn_id, attempt, candidate_digest,
                Disposition.UNKNOWN, "B_UNKNOWN", Concern.SEMANTIC, "",
            )

        try:
            subject = self._build(prepared, candidate, attempt)
            if (getattr(subject, "schema", None) != B_REQUEST
                    or getattr(subject, "request", None) is not prepared.request
                    or getattr(subject, "response", None) is not candidate):
                return unknown()
            result = self._evaluate(subject)
            if (getattr(result, "schema", None) != B_DECISION
                    or type(getattr(result, "decision", None)) is not str
                    or getattr(result, "evidence_class", None) != B_EVIDENCE
                    or getattr(result, "authorizes_effects", None) is not False
                    or getattr(result, "updates_memory", None) is not False
                    or getattr(result, "proves_subjective_state", None) is not False):
                return unknown()
            decision = Disposition(result.decision)
            reasons = result.reason_codes
            guidance = result.revision_guidance
            if (type(reasons) is not tuple or type(guidance) is not tuple
                    or any(type(x) is not str for x in (*reasons, *guidance))
                    or any(len(x.encode("utf-8")) > 1024 for x in reasons)
                    or len(guidance) > 8):
                return unknown()
            hint = ""
            if decision is Disposition.REVISE and guidance:
                if len(guidance) != 1:
                    return unknown()
                hint = guidance[0]
                if len(hint.encode("utf-8")) > 256:
                    return unknown()
            return ReviewVerdict(
                CONTRACT, turn_id, attempt, candidate_digest,
                decision, "B_" + decision.value, Concern.SEMANTIC, hint,
            )
        except Exception:
            return unknown()
