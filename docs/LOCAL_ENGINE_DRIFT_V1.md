# Local engine drift harness V1

Status: **source implementation and local tests; no installation or behavioral qualification implied.**

The sole Vera adapter remains the model-neutral `UniversalAdapter`.
`transports/local_chat.py` implements replaceable HTTP wire plumbing;
it is not a second identity adapter. Only numeric loopback IP addresses
are accepted, the connection follows no redirects, no credentials are used,
and engine timeouts do not automatically retry. No protected effects execute.

`vera_adapter.drift.run_unrescued` freezes the exact `AdapterRequest.ir`
for each engine, independently invokes the drivers, records errors without
rescue, and produces a SHA-256-bound observation manifest. It does not
score semantic identity or declare engines qualified.

## Example (explicit user-directed local inference, not run by tests)

From repo root, with two *already available* Ollama model IDs:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m tools.run_local_drift `
  --model qwen3:4b-instruct --model vera-local:latest `
  --prompt 'Distinguish source from installation, then explain why.' `
  --source-revision <exact-40-hex-Vera-Mono-commit> `
  --source-path packages/vera_identity/src/vera_identity/resources/architecture/identity/VERA_PROJECT_IDENTITY_V1.json `
  --output D:\VERA\portal-task-state\adapter-drift-001.json
```

The command *does* perform local inference and consumes GPU/CPU resources.
Do not use it while other model workloads hold the GPU. Output is
create-only and will not replace an earlier observation.

**Claim ceiling:** Two model IDs behind one Ollama runtime are different
models, **not independently implemented engines**. To test real engine
diversity, separately connect a distinct runtime (e.g. KoboldCPP exposing
OpenAI-compatible local chat) and record its independent process,
executable, version, model digest, port and provenance. Without those
observations, engine diversity remains UNKNOWN. Do not claim runtime
qualification or independent review from text similarity alone.

Canonical conversation items are currently untyped strings. The wire
driver treats all of them as user messages, never inferring assistant
roles from text. A typed conversation/role contract is a follow-up
design subject, not something to silently invent in transport.


## Cross-protocol targets (two individually configured endpoints)

The `--engines-file` mode uses a strict `VERA_ADAPTER_LOCAL_ENGINE_TARGETS_V1`
JSON file (see `examples/local-engine-targets.example.json`). Each of the
2-8 targets declares its own `engine_id`, `implementation_id`, `provider`,
`model`, `protocol` and `base_url`. Only numeric loopback HTTP hosts are
accepted; unsupported protocols, extra fields, duplicate IDs and invalid
target values fail before dispatch. The runner freezes a SHA-256 digest of
the manifest's exact input bytes in the output receipt.

```powershell
python -B -m tools.run_local_drift `
  --engines-file examples/local-engine-targets.example.json `
  --prompt 'What does this evidence prove?' `
  --source-revision <exact-40-hex-Vera-Mono-commit> `
  --source-path packages/vera_identity/src/vera_identity/resources/architecture/identity/VERA_PROJECT_IDENTITY_V1.json `
  --output D:\VERA\portal-task-state\two-engines-unrescued.json
```

The example's second endpoint is illustrative; its service and model
are NOT known to be installed or running. Live probes are opt-in and
require two reachable authorized endpoints. The manifest merely declares
implementation identity; it is not evidence of distinct underlying
executables, runtime processes, versions, model artifacts, or engines.
Every produced receipt says `engine_diversity_verification=NOT_ESTABLISHED`,
regardless of the strings in `implementation_id`. Independent runtime
identity requires separate host-side process/executable/version/artifact
readback and independent evaluation bound to the frozen input.
`source_revision` and `SourceRef` are declared attribution, not live
repository verification. There is no rescue feedback between trials.


## Receipt publication durability

The writer now flushes and fsyncs a same-directory temporary file, then
uses exclusive hard-link creation to publish a complete receipt without
replacing existing evidence. The temporary link is removed afterward.
On filesystems without atomic hard-link support it fails closed rather
than performing a non-atomic fallback. The published file is read back.
Its SHA-256 is an integrity checksum for accidental/unsanctioned changes,
**not** a signature or independent authentication of runtime observations.


## No-repeat preflight

If the requested output receipt path already exists, the CLI refuses the
invocation **before contacting any engine**. It also requires an existing
output parent directory. A concurrent writer is still guarded atomically
at hard-link publication; simultaneous runs are not a substitute for a
host-level lease controlling expensive engine calls.
