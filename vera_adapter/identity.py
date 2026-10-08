"""Portable identity and continuity primitives derived from training invariants."""
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class SourceRef:
    repository: str
    ref: str
    path: str
    evidence_class: str = "SOURCE_INSPECTION"

    def validate(self) -> None:
        if not self.repository.strip() or not self.ref.strip() or not self.path.strip():
            raise ValueError("identity source provenance is incomplete")
        if not self.evidence_class.strip():
            raise ValueError("identity source evidence class is missing")

@dataclass(frozen=True)
class IdentityCapsule:
    identity: Mapping[str, str]
    invariants: tuple[str, ...]
    continuity: tuple[str, ...] = ()
    sources: tuple[SourceRef, ...] = ()
    supersedes: tuple[str, ...] = ()

    def validate_provenance(self) -> None:
        if not self.sources:
            raise ValueError("identity capsule requires attributed source provenance")
        for source in self.sources:
            source.validate()

    def render(self) -> tuple[str, ...]:
        """Return provider-neutral context only after provenance is present."""
        self.validate_provenance()
        lines = tuple(f"{k}: {v}" for k, v in sorted(self.identity.items()))
        return lines + self.invariants + self.continuity
