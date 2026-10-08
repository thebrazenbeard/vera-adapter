"""Unrescued cross-engine observations; not model qualification."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable
from .core import AdapterRequest
from .provider import ProviderDriver, UniversalAdapter


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(data: object) -> str:
    return hashlib.sha256(canonical(data)).hexdigest()


@dataclass(frozen=True)
class EngineTarget:
    engine_id: str
    protocol: str
    driver: ProviderDriver
    implementation_id: str = ""


@dataclass(frozen=True)
class EngineObservation:
    engine_id: str
    protocol: str
    provider: str
    model: str
    status: str
    text: str | None
    error_class: str | None
    declared_implementation_id: str = ""


@dataclass(frozen=True)
class DriftEvidence:
    turn_id: str
    input_sha256: str
    source_revision: str
    observations: tuple[EngineObservation, ...]
    target_manifest_sha256: str | None = None

    def report(self) -> dict:
        data = {
            "schema": "VERA_ADAPTER_UNRESCUED_DRIFT_V1",
            "claim_ceiling": "LOCAL_OBSERVATION_NOT_BEHAVIORAL_QUALIFICATION",
            "independent_review": "NOT_ESTABLISHED",
            "baseline_rescue": False,
            "engine_diversity_verification": "NOT_ESTABLISHED",
            "target_manifest_sha256": self.target_manifest_sha256,
            "turn_id": self.turn_id,
            "input_sha256": self.input_sha256,
            "source_revision": self.source_revision,
            "observations": [asdict(item) for item in self.observations],
        }
        data["receipt_sha256"] = digest(data)
        return data


def run_unrescued(
    request: AdapterRequest, targets: Iterable[EngineTarget], *,
    source_revision: str, target_manifest_sha256: str | None = None,
) -> DriftEvidence:
    """Invoke each engine with the same immutable input; no inter-engine rescue."""
    if not source_revision or not source_revision.strip():
        raise ValueError("source revision required")
    expected = digest(asdict(request))
    request.ir.context()  # Fail provenance check before any engine dispatch.
    frozen_targets = tuple(targets)
    if not frozen_targets:
        raise ValueError("at least one engine required")
    seen: set[str] = set()
    for target in frozen_targets:
        if not target.engine_id.strip() or target.engine_id in seen:
            raise ValueError("engine IDs must be unique and nonempty")
        if not target.protocol.strip():
            raise ValueError("engine protocol required")
        seen.add(target.engine_id)
    records: list[EngineObservation] = []
    for target in frozen_targets:
        if digest(asdict(request)) != expected:
            raise ValueError("canonical input changed during drift run")
        driver = target.driver
        try:
            result = UniversalAdapter(driver).invoke(request)
        except Exception as exc:
            records.append(EngineObservation(
                target.engine_id, target.protocol, str(driver.provider),
                str(driver.model), "ERROR_NO_RETRY", None, type(exc).__name__,
                target.implementation_id,
            ))
        else:
            records.append(EngineObservation(
                target.engine_id, target.protocol, result.provider,
                result.model, "OBSERVED", result.text, None,
                target.implementation_id,
            ))
        if digest(asdict(request)) != expected:
            raise ValueError("engine mutated canonical input")
    return DriftEvidence(request.turn_id, expected, source_revision, tuple(records),
                         target_manifest_sha256)


def write_exclusive(path: Path, evidence: DriftEvidence) -> str:
    """Persist once; never overwrite a frozen observation."""
    report = evidence.report()
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report["receipt_sha256"]
