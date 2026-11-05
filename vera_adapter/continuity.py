"""Evidence-aware continuity selection.

Unbacked claims never become current truth and cannot erase verified truth merely
because they claim to be newer. A separate, host-admitted user correction may
invalidate an older value even if the replacement is not yet backed.
"""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class ContinuityFact:
    key: str
    value: str
    source_id: str
    ordinal: int
    exact: bool = False
    backing_available: bool = False

def resolve_current(
    facts: tuple[ContinuityFact, ...],
    *,
    admitted_correction: Callable[[ContinuityFact], bool] | None = None,
) -> dict[str, ContinuityFact]:
    """Resolve claims; only host-admitted corrections may retract backed values.

    ``admitted_correction`` must be supplied by a trusted owner outside this IR.
    Merely setting ``exact`` or a later ordinal does not admit a correction.
    """
    current: dict[str, ContinuityFact] = {}
    for fact in sorted(facts, key=lambda f: f.ordinal):
        if fact.backing_available:
            current[fact.key] = fact
        elif admitted_correction is not None and admitted_correction(fact) is True:
            current.pop(fact.key, None)
    return current
