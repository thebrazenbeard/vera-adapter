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
