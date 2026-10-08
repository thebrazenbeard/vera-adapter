"""Evidence-aware continuity selection.

Later explicit corrections supersede earlier values. An unverified newer exact
claim invalidates the older value without manufacturing a replacement.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ContinuityFact:
    key: str
    value: str
    source_id: str
    ordinal: int
    exact: bool = False
    backing_available: bool = False

def resolve_current(facts: tuple[ContinuityFact, ...]) -> dict[str, ContinuityFact]:
    current: dict[str, ContinuityFact] = {}
    for fact in sorted(facts, key=lambda f: f.ordinal):
        # Supersession happens before admissibility. A newer correction can make
        # the previous value obsolete even when the replacement cannot yet be
        # promoted as current truth.
        current.pop(fact.key, None)
        if fact.exact and not fact.backing_available:
            continue
        current[fact.key] = fact
    return current
