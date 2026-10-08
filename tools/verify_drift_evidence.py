"""Read-only drift receipt verifier. Never dispatches or loads an engine."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from vera_adapter.custody import EvidenceHold, verify_local_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_local_evidence(args.output)
    except EvidenceHold as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
