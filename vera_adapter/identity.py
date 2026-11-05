"""Portable identity and continuity primitives derived from training invariants."""
from dataclasses import dataclass
from typing import Mapping


class _FrozenIdentity(dict):
    """Detached read-only mapping with ordinary JSON/asdict compatibility."""

    def _readonly(self, *args, **kwargs):
        raise TypeError("identity is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _readonly

    def __ior__(self, other):
        return self._readonly(other)


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

    def __post_init__(self) -> None:
        if not isinstance(self.identity, Mapping):
            raise TypeError("identity must be a mapping")
        values = dict(self.identity)
        if any(type(key) is not str or type(value) is not str for key, value in values.items()):
            raise TypeError("identity keys and values must be strings")
        if any("\n" in part or "\r" in part for pair in values.items() for part in pair):
            raise ValueError("identity keys and values must be single-line strings")
        object.__setattr__(self, "identity", _FrozenIdentity(values))
        for field in ("invariants", "continuity", "supersedes"):
            entries = getattr(self, field)
            if type(entries) is not tuple or any(type(entry) is not str for entry in entries):
                raise TypeError(f"IdentityCapsule.{field} requires a string tuple")
        if type(self.sources) is not tuple or any(type(item) is not SourceRef for item in self.sources):
            raise TypeError("IdentityCapsule.sources requires SourceRef tuple")

    def validate_provenance(self) -> None:
        """Check citation shape only; never authenticate a repository or content."""
        if not self.sources:
            raise ValueError("identity capsule requires attributed source provenance")
        for source in self.sources:
            source.validate()

    def render(self) -> tuple[str, ...]:
        """Render attributed text; provider use additionally requires host verification."""
        self.validate_provenance()
        lines = tuple(f"{k}: {v}" for k, v in sorted(self.identity.items()))
        return lines + self.invariants + self.continuity
