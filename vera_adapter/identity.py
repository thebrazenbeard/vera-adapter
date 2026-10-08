"""Portable identity and continuity primitives derived from training invariants."""
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class SourceRef:
    repository: str
    ref: str
    path: str
    evidence_class: str = "SOURCE_INSPECTION"

@dataclass(frozen=True)
class IdentityCapsule:
    identity: Mapping[str, str]
    invariants: tuple[str, ...]
    continuity: tuple[str, ...] = ()
    sources: tuple[SourceRef, ...] = ()
    supersedes: tuple[str, ...] = ()

    def render(self) -> tuple[str, ...]:
        """Return provider-neutral context without inventing unsupported state."""
        lines = tuple(f"{k}: {v}" for k, v in sorted(self.identity.items()))
        return lines + self.invariants + self.continuity
