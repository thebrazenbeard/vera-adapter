"""Canonical provider-independent Vera intermediate representation."""
from dataclasses import dataclass
from typing import Callable
from .identity import IdentityCapsule
from .continuity import ContinuityFact, resolve_current

@dataclass(frozen=True)
class VeraIR:
    identity: IdentityCapsule
    continuity_facts: tuple[ContinuityFact, ...] = ()
    conversation: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    authority: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.identity) is not IdentityCapsule:
            raise TypeError("VeraIR.identity must be exactly IdentityCapsule")
        if type(self.continuity_facts) is not tuple or any(
            type(fact) is not ContinuityFact for fact in self.continuity_facts
        ):
            raise TypeError("VeraIR continuity requires canonical fact tuple")
        for field in ("conversation", "capabilities", "authority"):
            values = getattr(self, field)
            if type(values) is not tuple or any(type(value) is not str for value in values):
                raise TypeError(f"VeraIR.{field} requires string tuple")

    def context(
        self,
        *,
        admitted_correction: Callable[[ContinuityFact], bool] | None = None,
    ) -> tuple[str, ...]:
        current = resolve_current(self.continuity_facts, admitted_correction=admitted_correction)
        continuity = tuple(f"{key}: {current[key].value}" for key in sorted(current))
        return self.identity.render() + continuity
