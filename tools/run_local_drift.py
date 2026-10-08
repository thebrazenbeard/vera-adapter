"""Explicit opt-in local probe; separate model IDs do not prove engine diversity."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from vera_adapter.core import AdapterRequest
from vera_adapter.drift import EngineTarget, run_unrescued, write_exclusive
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.ir import VeraIR
from transports.local_chat import LocalChatDriver


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--protocol", choices=("ollama_chat", "openai_chat"), default="ollama_chat")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    if len(args.model) < 2 or len(set(args.model)) != len(args.model):
        parser.error("specify at least two different local model IDs")
    if re.fullmatch(r"[0-9a-fA-F]{40}", args.source_revision) is None:
        parser.error("source revision must be an exact 40-character commit SHA")
    source = SourceRef("thebrazenbeard/vera-mono", args.source_revision, args.source_path)
    ir = VeraIR(
        IdentityCapsule({"name": "Vera"}, ("truth over fabrication",), sources=(source,)),
        conversation=(args.prompt,),
    )
    request = AdapterRequest("local-drift-001", ir)
    targets = [
        EngineTarget(
            "local-model-" + str(i), args.protocol,
            LocalChatDriver(
                provider="local-model-server", model=model,
                base_url=args.base_url, protocol=args.protocol,
            ),
        )
        for i, model in enumerate(args.model, start=1)
    ]
    evidence = run_unrescued(request, targets, source_revision=args.source_revision)
    receipt = write_exclusive(args.output, evidence)
    print("Local model observations; distinct engine runtimes NOT established")
    print("receipt_sha256=" + receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
