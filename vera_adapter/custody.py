"""Read-only custody checks for local engine drift attempts.

No model inference, effects, authentication, or independent behavioral review.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .attempt import SCHEMA as CLAIM_SCHEMA, attempt_claim_path
from .drift import digest


class EvidenceHold(ValueError):
    """Local evidence cannot establish a complete, internally consistent run."""


@dataclass(frozen=True)
class EvidenceCheck:
    status: str
    claim_sha256: str
    receipt_sha256: str
    observation_count: int


def _read_json(path: Path, label: str, *, limit: int = 32_000_000) -> dict:
    if not path.is_file() or path.stat().st_size > limit:
        raise EvidenceHold(f"{label}: missing or oversized")
    try:
        data: Any = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise EvidenceHold(f"{label}: unreadable JSON") from exc
    if not isinstance(data, dict):
        raise EvidenceHold(f"{label}: expected JSON object")
    return data


def _verify_self_hash(data: dict, key: str, label: str) -> str:
    claimed = data.get(key)
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise EvidenceHold(f"{label}: missing SHA-256")
    fields = dict(data)
    fields.pop(key)
    if digest(fields) != claimed:
        raise EvidenceHold(f"{label}: SHA-256 mismatch")
    return claimed


def verify_local_evidence(output: Path) -> EvidenceCheck:
    """Verify intrinsic custody only; self-hashes cannot authenticate a signer."""
    requested = Path(output)
    if requested.is_symlink():
        raise EvidenceHold("output: symbolic link not permitted")
    resolved = requested.resolve()
    claim_path = attempt_claim_path(resolved)
    if claim_path.is_symlink():
        raise EvidenceHold("claim: symbolic link not permitted")
    claim = _read_json(claim_path, "claim")
    claim_sha = _verify_self_hash(claim, "claim_sha256", "claim")
    if claim.get("schema") != CLAIM_SCHEMA:
        raise EvidenceHold("claim: unexpected schema")
    if claim.get("output_path") != str(resolved):
        raise EvidenceHold("claim: destination mismatch")
    if claim.get("status") != "CLAIMED_BEFORE_DISPATCH_NOT_PROOF_OF_ENGINE_EXECUTION":
        raise EvidenceHold("claim: invalid status")
    if claim.get("retry_policy") != "NO_AUTOMATIC_RETRY":
        raise EvidenceHold("claim: invalid retry policy")
    declared = claim.get("targets")
    if not isinstance(declared, list) or not declared:
        raise EvidenceHold("claim: empty targets")

    if not resolved.exists():
        raise EvidenceHold("HOLD_CLAIMED_NO_RESULT: outcome ambiguous")
    receipt = _read_json(resolved, "receipt")
    receipt_sha = _verify_self_hash(receipt, "receipt_sha256", "receipt")
    if receipt.get("schema") != "VERA_ADAPTER_UNRESCUED_DRIFT_V1":
        raise EvidenceHold("receipt: unexpected schema")
    if receipt.get("baseline_rescue") is not False:
        raise EvidenceHold("receipt: rescue status unexpected")
    if receipt.get("engine_diversity_verification") != "NOT_ESTABLISHED":
        raise EvidenceHold("receipt: unauthorized engine diversity claim")
    for key in ("turn_id", "input_sha256", "source_revision", "target_manifest_sha256"):
        if receipt.get(key) != claim.get(key):
            raise EvidenceHold(f"receipt: {key} differs from claim")
    if receipt.get("attempt_claim_sha256") != claim_sha:
        raise EvidenceHold("receipt: claim digest mismatch")
    observations = receipt.get("observations")
    if not isinstance(observations, list) or len(observations) != len(declared):
        raise EvidenceHold("receipt: target count mismatch")

    seen: set[str] = set()
    for expected, actual in zip(declared, observations, strict=True):
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            raise EvidenceHold("receipt: invalid target entry")
        engine_id = expected.get("engine_id")
        if not isinstance(engine_id, str) or engine_id in seen:
            raise EvidenceHold("claim: invalid or repeated engine ID")
        seen.add(engine_id)
        for key in ("engine_id", "protocol", "provider", "model",
                    "declared_implementation_id"):
            if actual.get(key) != expected.get(key):
                raise EvidenceHold(f"receipt: changed target {key}")
        status = actual.get("status")
        if status == "OBSERVED":
            if not isinstance(actual.get("text"), str) or not actual["text"]:
                raise EvidenceHold("receipt: observed output missing")
            if actual.get("error_class") is not None:
                raise EvidenceHold("receipt: observed output has error")
        elif status == "ERROR_NO_RETRY":
            if actual.get("text") is not None or not isinstance(actual.get("error_class"), str):
                raise EvidenceHold("receipt: malformed failure")
        else:
            raise EvidenceHold("receipt: unsupported target status")

    return EvidenceCheck(
        "PASS_INTERNAL_CUSTODY_ONLY", claim_sha, receipt_sha, len(observations)
    )
