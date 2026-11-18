# Midflight ChatGPT Text Advisory V1 — Engineer A source handoff

Status: SOURCE_ONLY / OPT-IN SYNTHETIC / NO NATIVE PLUGIN INSTALL / NO HOST INTERCEPTION.
Owner: Engineer A in the existing thebrazenbeard/vera-adapter repository, isolated draft PR #13. Engineer B owns semantic rules and independent benchmark admission; no B source has been changed here.

## Authority, current source and user priority

- User's current text-chat-first priority was recorded as sanitized coordination in chat-communication-bus#397 comment 6978981320; A replied in comment 6979128705. A review does not prove B acceptance.
- Vera Adapter main source pinned at 003d04f877f640791a3324eb360902f5db5eb5c9; Engineer A host draft originally at 1bbd09855d42cc6ef9db809aa90cf8f6169e385d. New additive A files are owned only on its draft branch.
- B semantic PR #14 at 30139e7c5451186e1d10221c58d21ed8d4a3213f (tree c40b78203d3ccc673af3e023c4068ac50f17479f), semantic_correction.py raw source SHA256 04c9b6237f6c0b0d08a55ab7bdea7178b47877ffcac61ee0c50ee78e1cd09117.
- F.U.C.K.U.P. source pin 670fe3282cfddae6d7a1d9c851b80cd6884df6a4, DriftGuard source pin 28e54e0291be60887ef3f20599ec7d7ac286dab0. The B fixture signer/currentness snapshot is NOT an authenticated host issuer.
- Public chat-communication-bus is not a private mailbox. Blotter shared-lane logs never contain full candidate text, source corrections, credentials, or intimate material.

## Opt-in, observable seam

ChatAdvisory (vera_adapter/chat_advisory.py) maintains only host-claimed turn registration and observed synchronous review method calls in one process. The versioned receipt is VERA_CHAT_ADVISORY_V1. It tracks attempted/mentioned, actually invoked, reviewed, disposition and final-delivery-UNOBSERVED independently.

Only an actual call into ChatAdvisory.review increments the invoked count. The user adding an @mention is not evidence the host called a tool; if the host failed to register that turn, this fixture cannot even count it as a miss. Model-generated statements such as 'I checked the plugin' are not independently verifiable receipts.

ReviewVerdict (VERA_MIDFLIGHT_HOST_GATE_V1) binds complete candidate digest, exact turn, attempt and typed PASS/REVISE/BLOCK/UNKNOWN result; untrusted or malformed replies become UNKNOWN. The review receipt never authorizes tools or suppresses the ChatGPT UI; proposed actions are retained as data and not executed.

EngineerBReviewPort (vera_adapter/midflight_b_bridge.py) builds a current ReviewRequest through an injected host callback and structurally validates an exact B ReviewDecision V1. It requires input object identity to match the withheld candidate and request, rejects any purported effect/memory/subjective-state grant, and maps B reason texts to fixed safe A reason codes. It reports B semantic BLOCK as semantic withholding, not as a fabricated hard host authorization decision. A constructed digest is not proof the B callback was honest or independent.

## Reproduced Lappy evidence

- Windows Lappy Python 3.12.10 isolated A PR13 checkout: 33 original A tests PASS, 12 new ChatAdvisory tests PASS, 10 new Engineer B translation tests PASS, and 4 source-only plugin package tests PASS before final aggregate run.
- Two observed RED->GREEN cycles: ChatAdvisory behavior missing, then 12 tests passed; B bridge behavior missing, then 10 tests passed. Plugin package missing produced RED; its 4 tests then passed.
- A/B actual-source composition used B PR14 exact LF source bytes in a separate disposable test harness, without changing B's branch. A host denied forbidden synthetic direct address (0 writes), delivered one clean synthetic answer unchanged (1 write), and withheld output on missing source epoch (0 writes). It did not run a real model.
- Normal Windows B PR14 checkout with core.autocrlf=true produced one SHA256 seal failure in B's 56-test suite. Raw LF-preserving B checkout at the same exact head produced 56/56 PASS; the B source SHA256 matches the sealed expected hash. This is an EOL-sensitive test/custody portability issue, not evidence B's Git source changed.

## Package and effect boundaries

plugin/vera-midflight-advisory/plugin.json plus skills/vera-midflight-advisory form a source-only candidate Plugin Creator package. The private installed vera-conscience 0.1.0 was inspected read-only; it was NOT replaced, updated, copied or installed as this new package.

Ordinary ChatGPT MCP tools cannot force selection just because the user tags them, cannot obtain a guaranteed pre-delivery hook, and cannot undo streaming or earlier provider-side effects. A real host-managed proxy with disabled/brokered tools is necessary for enforced delivery. A ChatGPT plugin experiment first needs a genuinely connected action and per-turn receipt capture under explicit user authority; source-only file tests are not real ChatGPT tool-call qualification.

## Next bounded verification

1. Add an actual private, version-pinned reviewer action with explicit permitted candidate/body privacy, issuer binding and user opt-in; separately authorize any plugin install or replacement.
2. In ordinary text chat, user explicitly tags it on each trial turn. Observe real tool calls, count tagged attempts vs invocations, measure B's false positives, correction application and good-response preservation, and separately capture actual final display bytes if the host exposes them. Without such bytes, report final-delivery UNKNOWN.
3. Feed only measured per-turn metrics into DriftGuard's exact release benchmark, preserving B's independent source/holdout ownership.
4. Keep the existing host-buffered API/local GGUF path as a later distinct qualification stage; Lappy being online does not grant model-service mutation, paid calls, plugin installation, merge, training or native control replacement.

Release: HOLD pending real ChatGPT invocation and independent authenticity/currentness/host-delivery qualification.
