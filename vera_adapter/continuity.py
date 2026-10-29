"""Review candidate continuity imports without changing memory, identity, or tools.

Authorization must come from an independently trusted verifier supplied by the
host runtime, not from candidate text or a model-produced consent flag. A True
result means eligibility for *later* governed admission, not a completed write.
"""
from dataclasses import dataclass
from hashlib import sha256
from typing import Callable


@dataclass(frozen=True)
class ContinuityCandidate:
    record_id: str
    source_kind: str
    source_ref: str
    source_actor: str
    scope: str
    target_state: str
    content: str
    claims_lived_experience: bool = False


@dataclass(frozen=True)
class AdmissionResult:
    admissible: bool
    reason: str
    provenance_class: str


# The host is responsible for authenticating the actual human authorization,
# validating its scope/expiry, and binding it to these exact arguments.
Verifier = Callable[[str, str, str, str, str, str, str], bool]

_ALLOWED_SOURCES = frozenset({"USER_SUPPLIED", "EXTERNAL_SOURCE", "MODEL_OUTPUT"})
_ALLOWED_TARGETS = frozenset({"semantic_memory", "working_memory"})
_PROTECTED_TARGETS = frozenset({"identity_critical", "self_model"})


def inspect_continuity_import(
    candidate: ContinuityCandidate, verifier: Verifier | None = None,
) -> AdmissionResult:
    """Return a read-only eligibility decision, never a state mutation.

    A caller must not treat this result as an authorization to write or claim
    a memory. Identity changes require a different, separately reviewed path.
    """
    def reject(reason: str) -> AdmissionResult:
        return AdmissionResult(False, reason, candidate.source_kind)

    if any(not isinstance(v, str) or not v.strip() for v in (
        candidate.record_id, candidate.source_ref, candidate.source_actor,
        candidate.scope, candidate.content,
    )):
        return reject("MISSING_ATTRIBUTABLE_PROVENANCE")
    if not isinstance(candidate.source_kind, str) or candidate.source_kind not in _ALLOWED_SOURCES:
        return reject("UNRECOGNIZED_SOURCE_CLASS")
    if not isinstance(candidate.target_state, str):
        return reject("TARGET_NOT_ELIGIBLE_FOR_IMPORT")
    if candidate.target_state in _PROTECTED_TARGETS:
        return reject("IDENTITY_CHANGE_REQUIRES_SEPARATE_CONTRACT")
    if candidate.target_state not in _ALLOWED_TARGETS:
        return reject("TARGET_NOT_ELIGIBLE_FOR_IMPORT")
    if candidate.claims_lived_experience:
        return reject("IMPORTED_NOT_LIVED")
    if verifier is None or not callable(verifier):
        return reject("EXTERNAL_AUTHORIZATION_REQUIRED")
    try:
        accepted = verifier(candidate.record_id, candidate.scope,
                            candidate.source_ref, candidate.source_actor,
                            candidate.source_kind, candidate.target_state,
                            sha256(candidate.content.encode("utf-8")).hexdigest())
    except Exception:
        return reject("AUTHORIZATION_UNVERIFIABLE")
    if accepted is not True:
        return reject("EXTERNAL_AUTHORIZATION_DENIED")
    return AdmissionResult(True, "ELIGIBLE_FOR_DOWNSTREAM_REVIEW_ONLY", candidate.source_kind)
