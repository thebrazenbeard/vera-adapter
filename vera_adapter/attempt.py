"""Create-only, durable pre-dispatch claim for local drift attempts.

A claim is not a runtime effect receipt. Interrupted runs are ambiguous and
must never be retried automatically at the same output path.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from .core import AdapterRequest
from .drift import EngineTarget, digest


SCHEMA = "VERA_ADAPTER_LOCAL_ATTEMPT_CLAIM_V1"


def attempt_claim_path(output: Path) -> Path:
    return Path(str(Path(output).resolve()) + ".attempt.json")


def claim_attempt(
    output: Path,
    request: AdapterRequest,
    targets: tuple[EngineTarget, ...],
    *,
    source_revision: str,
    target_manifest_sha256: str | None,
) -> str:
    """Exclusively reserve output before any engine call; keep claim forever.

    An incomplete claim is an ambiguous attempt, not a stale lock to delete.
    """
    if Path(output).is_symlink():
        raise ValueError("output symlink prohibited")
    output = Path(output).resolve()
    if not output.parent.is_dir():
        raise ValueError("output parent directory does not exist")
    if output.exists() or output.is_symlink():
        raise FileExistsError("output already exists; do not dispatch")
    if not targets:
        raise ValueError("at least one engine required")
    if not source_revision.strip():
        raise ValueError("source revision required")

    # All validation precedes any claim or engine call.
    request.ir.context()
    if len({x.engine_id for x in targets}) != len(targets):
        raise ValueError("duplicate engine ID")
    if any(not x.engine_id.strip() or not x.protocol.strip() for x in targets):
        raise ValueError("invalid engine ID or protocol")
    if any(not str(x.driver.provider).strip() or not str(x.driver.model).strip()
           for x in targets):
        raise ValueError("engine provenance missing")

    claim = {
        "schema": SCHEMA,
        "status": "CLAIMED_BEFORE_DISPATCH_NOT_PROOF_OF_ENGINE_EXECUTION",
        "output_path": str(output),
        "turn_id": request.turn_id,
        "input_sha256": digest(asdict(request)),
        "source_revision": source_revision,
        "target_manifest_sha256": target_manifest_sha256,
        "retry_policy": "NO_AUTOMATIC_RETRY",
        "targets": [
            {
                "engine_id": x.engine_id,
                "protocol": x.protocol,
                "provider": x.driver.provider,
                "model": x.driver.model,
                "declared_implementation_id": x.implementation_id,
            } for x in targets
        ],
    }
    claim["claim_sha256"] = digest(claim)
    contents = (json.dumps(claim, sort_keys=True, indent=2) + "\n").encode("utf-8")

    path = attempt_claim_path(output)
    # O_EXCL is the cross-process gate, before model inference.
    with path.open("xb") as handle:
        handle.write(contents)
        handle.flush()
        os.fsync(handle.fileno())
    if path.read_bytes() != contents:
        raise OSError("attempt claim readback mismatch; attempt is ambiguous")
    return claim["claim_sha256"]
