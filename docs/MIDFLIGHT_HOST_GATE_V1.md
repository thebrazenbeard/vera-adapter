# Vera Adapter — Midflight Host Gate V1 (Engineer A)

Status: **SOURCE ONLY / SYNTHETIC / DRAFT / NO DEPLOYMENT**. This work belongs in `thebrazenbeard/vera-adapter`, not a parallel primary adapter repository. It changes no `core.py`, provider keys, permissions, live ChatGPT runtime, training, or installed plugins. $0 compute; VN1 Windows Python 3.13 synthetic test host (Lappy reported off).

## Exact current source pins and ownership

- Vera Adapter `main@003d04f877f640791a3324eb360902f5db5eb5c9`, `vera_adapter/core.py` blob `4cdf2d2232804b8c70b5c882d63cb22376247cca`. PR #11 `5bf8b55520e4ba050bff227e4b52da2d5cd0558b` and PR #12 `74f0938b2a87786b6c4419bf89de1bbb70f1249f` change core identity/provenance; this branch adds independent files only.
- F.U.C.K.U.P. `main@670fe3282cfddae6d7a1d9c851b80cd6884df6a4`: `bindings.py` blob `48029c1ab1cbbbb8af862c0599c1914d1bc327ec`; `session_preflight.py` blob `260e2c4bd5d15df231379d0639da34b34ebe95b4`. Its `load_reference_session_preflight`, `verify_materialized_prompt`, and `verify_dispatch_currentness` remain the sole source of correction selection, materialization and revocation checks. Do not reconstruct their authority logic.
- DriftGuard `main@28e54e0291be60887ef3f20599ec7d7ac286dab0`; use its `DRIFTGUARD_CI_GATE_RESULT_V1` for exact benchmark release admission, not this gate's per-candidate `PASS`.
- Vera Eros B semantic draft PR #4 `fe6d7442dc03d93b945ab19d578eb052775b1b13`: existing `vera-eros.semantic-record.v1` and synthetic B-only semantic/replay gates. No B code or semantic policy implemented here.
- Blotter separate draft PRs #45/#46: private principal verifier default deny and synthetic file-receipt integrity, not installed/private native ChatGPT per-chat identities.
- Chat Communication Bus `main@eb315a5612ae99aadddb397891ffcf3a2b0433a6` is PUBLIC, manual-only/source coordination, not a private authentication bus. The Blotter tunnel was unavailable during this iteration; no private-channel assertion.
- Pre-Active run contract affinity: `docs/RUN_CONTRACT_AFFINITY.md` blob `962fb773721d191cec20144c627c39fdc7bebd39` warns a source upgrade is not a run migration. Portal owns orchestration; Pre-Active owns observation/wake. No runtime route was changed.

## Versioned host contract

`VERA_MIDFLIGHT_HOST_GATE_V1` is the exact `ReviewVerdict.schema`. `Disposition` is `PASS | REVISE | BLOCK | UNKNOWN`; `Concern` is `HARD | SEMANTIC`. The reviewer must return an exact typed `ReviewVerdict` with matching `turn_id`, integer `attempt`, SHA256 of the exact buffered text, disposition, reason code, concern and bounded revision hint. An impostor, stale/foreign digest, wrong turn, unknown schema, malformed response or unavailable reviewer becomes **WITHHELD**, never silently PASS. The verifier interface is injectable; Engineer B controls actual semantic rules and benchmark qualification.

`PreparedTurn` is issued by a host-owned `CorrectionPort` and bound to the exact immutable copied `AdapterRequest`, a nonempty correction reference/source reference, and digest. Its `current(prepared, phase)` is checked before each model dispatch AND just before delivery. A definitive false currentness result is **BLOCKED**; unavailable/ambiguous currentness is **WITHHELD**. A semantic reviewer never grants correction activation, tools, network, file access, provider effects or permission to publish.

`CandidatePort.generate` must produce `AdapterResponse` or `BufferedStream`, preserving turn/provider/model provenance and optional `proposed_actions`; no tool effects are executed by this module. All stream chunks are collected into a bounded private buffer (64 KiB UTF-8) before review. No early response is sent to `DeliveryPort`. Revise at most `max_revisions` (default 1, limit 0..3), and reject unannounced provider/model substitution on revision. A strict PASS and fresh delivery currentness precede **one** publish call. Only an exact `DeliveryAck` for the same turn/digest yields **DELIVERED**. An exception/invalid ack after calling publish is **DELIVERY_UNKNOWN**, never silently retried or mislabeled as BLOCKED.

`ReplayPort.claim` happens before preparation. The included single-process `InMemoryReplay` and `InMemoryDelivery` are ONLY synthetic fixtures. A real host must provide durable/atomic turn-and-effect custody, revocation-aware commit, protected replay records, and transactional network delivery or explicit ambiguity reconciliation.

`AuditRecord` contains stage, SHA256 turn fingerprint and candidate digest, a fixed reason-code vocabulary, and numeric proposed-action count. It excludes candidate text, prompt, correction message, reviewer reason text, private semantic state, credentials and sensitive proposed-action payloads. Even `ReviewVerdict.reason_code` is not copied into shared telemetry.

`F.U.C.K.U.P.` bridge: `FuckupPreflightPort` calls upstream preflight / prompt materialization / dispatch-currentness functions and binds the exact returned correction digest to this host turn. It does not modify instructions or claim provider consumption. Its test fixture mocks those functions; **real F.U.C.K.U.P. datastore, protected source and outgoing provider-message readback remain unqualified**.

## Explicit verified test ceiling and negative controls

Run `python -B -m unittest discover -s tests -p "test_*.py" -v` in an isolated clean checkout with Python 3.13 or later. The host gate tests include: never publishing a blocked candidate; unchanged exact PASS; bounded revision then PASS; exhaustion; malformed/offline/unknown verifier; definitive stale/revoked preflight before dispatch/delivery; duplicate turn; mismatched review digest/turn; interrupted/oversized stream; proposed-action non-execution; provider/model substitution; reviewer reason leakage; immutable host identity/authority; and delivery ack ambiguity. The bridge tests verify invocation shape with **mocked** F.U.C.K.U.P. exports only. A passing synthetic test proves neither true semantic accuracy nor external provider execution.

> Hostile challenge: a `PASS` from a corrupted or untrusted callback can permit unacceptable text. The host must bind the verifier to a pinned, independently qualified B revision; source tests cannot prove its accuracy, independence, or honest runtime execution.

> Hostile challenge: a producer/reviewer that executes tools BEFORE returning is outside the text gate. A production model client must disable all provider-side tools (or route EVERY tool call through a separate authorized effect broker). Do not claim this Python function can retract already-run shell/network/model actions.

> Hostile challenge: currentness at `delivery` still has a time-of-check/time-of-use gap unless the actual delivery sink atomically checks revocation at commit. Network exceptions after write are genuinely ambiguous. Stream previews, model event consumers, logs and client UIs must all be behind the proxy for real enforcement.

## Real intervention surfaces (sources checked November 18, 2026)

| Surface | Evidence | Binding limit |
| --- | --- | --- |
| Ordinary ChatGPT MCP skill/plugin | [OpenAI MCP tools](https://developers.openai.com/api/docs/guides/tools-connectors-mcp) and [agents integrations](https://developers.openai.com/api/docs/guides/agents/integrations-observability) | Model/host invokes an approved tool; **no guaranteed global pre-display interceptor** for ordinary ChatGPT UI. Vera Conscience's review workflow is advisory, not an in-flight output gate. |
| OpenAI Responses API / Agents SDK | [Guardrails and human approvals](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals), [streaming](https://developers.openai.com/api/docs/guides/streaming-responses) | Developer controls application display, tool adapters and output guardrails; buffer until approved, or early streamed text has already escaped. Paid provider calls were NOT made. |
| GPT-6 WebSocket steering | [Mid-turn steering](https://developers.openai.com/api/docs/guides/steering), [WebSocket API](https://developers.openai.com/api/docs/guides/websocket-mode) | `response.steer` queues a steering continuation; it does not retract text already sent to the application or undo a tool already started. Not tested with provider account. |
| Local llama.cpp | [llama-server reference](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) | Supports OpenAI-style chat and SSE; a host proxy can buffer/abort provider generation while keeping all client output gated. No local model probe yet. |
| Local KoboldCpp | [KoboldCpp API](https://github.com/LostRuins/koboldcpp.net/blob/main/src/content/docs/docs/api/endpoints.mdoc) | SSE `/api/extra/generate/stream`, abort via `/api/extra/abort`; abort does NOT retract already sent chunks. Host proxy must be sole delivery path. No KoboldCpp runtime tested this iteration. |

Correction research: [Huang et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/8b4add8b0aa8749d80a34ca5d941c355-Abstract-Conference.html) challenges intrinsic self-correction without external feedback; [SCORE, ACL Findings 2024](https://aclanthology.org/2024.findings-acl.924/) reports improvement with a strong verifier, not an arbitrary weak reviewer; [Kamoi et al., TACL 2024](https://aclanthology.org/2024.tacl-1.78/) synthesizes the benefit of reliable external feedback and limits of prompted-only self-correction. Thus V1 uses an injectable external review contract and **does not** pretend model self-agreement is independent proof.

## Demonstrated vs pending

| Claim | Evidence class | Result |
| --- | --- | --- |
| Blocked synthetic output never reaches memory delivery sink | ISOLATED_SIMULATION (test) | Reproducible in VN1 Python |
| Approved synthetic bytes pass intact, and one reviewed revision may pass | ISOLATED_SIMULATION | Reproducible in VN1 Python |
| Malformed verifier, revoked correction, duplicate turn and broken stream cannot silently PASS | ISOLATED_SIMULATION | Reproducible in VN1 Python |
| Existing adapter tests still pass | SOURCE_TEST | Must run fresh complete suite after changes |
| F.U.C.K.U.P. live correction readback | REAL_HOST_PROBE | NOT TESTED: fake bridge functions in synthetic harness |
| Engineer B semantic accuracy / DriftGuard benchmark admission | BENCHMARK | NOT TESTED; B owns decisions, DriftGuard owns release admission |
| GPU/local GGUF provider and genuine abort | REAL_MODEL_EXECUTION | NOT TESTED (Lappy off) |
| Authenticated native ChatGPT output interception | INSTALLED_HOST_EFFECT | NOT IMPLEMENTED / NOT QUALIFIED |
| Cross-process transactional delivery and irrevocable effect suppression | REAL_SYSTEM_PROBE | NOT QUALIFIED; sink is process-local fixture |

## Next bounded verification

**Local model:** When an authorized local GGUF service is online, bind the HTTP/SSE stream to a *private-only* proxy with tool routes disabled; run one synthetic forbidden marker and one innocuous PASS behind an exclusively gated client. Verify exact server/version/model hash, abort behavior, client output bytes, request/response logs, and no bypass route. No installation or paid service without Patrick's exact permission.

**ChatGPT-facing advisory:** In a separate reviewed private-plugin version, present `PASS/REVISE/BLOCK/UNKNOWN` as explicitly requested Vera Conscience guidance *before the assistant chooses to answer*, with provenance. Do not call that guaranteed native midflight interception, native plugin replacement or independent older-GPT execution.
