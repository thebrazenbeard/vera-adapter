"""Canonical provider-independent Vera intermediate representation."""
from dataclasses import dataclass
from .identity import IdentityCapsule
from .continuity import ContinuityFact, resolve_current

@dataclass(frozen=True)
class VeraIR:
    identity: IdentityCapsule
    continuity_facts: tuple[ContinuityFact, ...] = ()
    conversation: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    authority: tuple[str, ...] = ()

    def context(self) -> tuple[str, ...]:
        current = resolve_current(self.continuity_facts)
        continuity = tuple(f"{key}: {current[key].value}" for key in sorted(current))
        return self.identity.render() + continuity
