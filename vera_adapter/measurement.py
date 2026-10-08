"""Continuity measurement without declaring identity equivalence."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ContinuityMeasurement:
    invariant_total: int
    invariant_matches: int
    correction_total: int
    correction_matches: int
    @property
    def invariant_rate(self) -> float:
        return 1.0 if self.invariant_total == 0 else self.invariant_matches / self.invariant_total
    @property
    def correction_rate(self) -> float:
        return 1.0 if self.correction_total == 0 else self.correction_matches / self.correction_total

def measure(expected_invariants: tuple[str, ...], observed: tuple[str, ...], expected_corrections: dict[str, str], observed_corrections: dict[str, str]) -> ContinuityMeasurement:
    return ContinuityMeasurement(len(expected_invariants), sum(x in observed for x in expected_invariants), len(expected_corrections), sum(observed_corrections.get(k) == v for k, v in expected_corrections.items()))
