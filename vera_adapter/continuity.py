"""Evidence-aware continuity selection.

Later explicit corrections supersede earlier values; exact claims require backing.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ContinuityFact:
    key: str
    value: str
    source_id: str
    ordinal: int
    exact: bool = False
    backing_available: bool = True

def resolve_current(facts: tuple[ContinuityFact, ...]) -> dict[str, ContinuityFact]:
    current: dict[str, ContinuityFact] = {}
    for fact in sorted(facts, key=lambda f: f.ordinal):
        if fact.exact and not fact.backing_available:
            continue
        current[fact.key] = fact
    return current
