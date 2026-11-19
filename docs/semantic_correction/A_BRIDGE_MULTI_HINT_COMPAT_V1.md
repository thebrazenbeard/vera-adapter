# Engineer B → Engineer A: Multi-hint V1 bridge compatibility review

Source-only, synthetic, 2026-11-18. Neither draft is merged/installed.

## Exact interface subjects

- B original source: vera-adapter draft PR #14, base head 30139e7c5451186e1d10221c58d21ed8d4a3213f, semantic_correction.py SHA-256 04c9b6237f6c0b0d08a55ab7bdea7178b47877ffcac61ee0c50ee78e1cd09117. B's frozen H3 DriftGuard result belongs only to this exact semantic evaluator version.
- A exact source: vera-adapter draft PR #13 at a6b0405cd1ee9f83ea8c25798a9b9cd605518c8b; midflight_b_bridge.py Git blob 695d83e98016ba9a2da7f5051c13bf4a41427a24.
- No source file in A's PR is mutated. Both are source-only, not an authorized native ChatGPT interceptor.

## Actual reproducible failure

A's EngineerBReviewPort deliberately accepts only **one** revision guidance string for a B REVISE. B's frozen ReviewDecision V1 can contain multiple applicable rules and independent suggestions. In a wholly fictional current situation that needs both an apology-loop correction and an unrequested-philosophical-detour correction, B returns REVISE with 2 static guidance strings, but A's bridge maps it to UNKNOWN/B_UNKNOWN. The behavior fails closed, but an otherwise actionable contextual correction gets withheld.

Test the exact A module by setting VERA_ADAPTER_A_BRIDGE_SOURCE_ROOT to an independently pinned A PR #13 checkout and running:

    py -3.12 -B -m unittest -v tests.test_semantic_a_bridge_optin

If A source is not supplied, these optional tests **SKIP**; a skip is not interface qualification.

## B-owned nonconflicting remedy

New module vera_adapter/semantic_bridge_compat.py exports review_for_engineer_a_v1(request, fixture_verifier). It calls the **unchanged** B V1 evaluator and projects a multi-hint REVISE into exactly one bounded, deterministic, ordered statement. The projection preserves all individual content, applicable IDs, reason codes and nonauthority flags. It does not infer a personal desire, change privacy or correction state, or authorize delivery.

If consolidation would exceed 256 UTF-8 bytes, contains a malformed/blank hint, or exceeds eight inputs, the output is UNKNOWN/BRIDGE_GUIDANCE_TOO_LARGE, with zero guidance rather than silently dropping a needed correction. PASS/BLOCK/UNKNOWN results remain unchanged. The A bridge remains responsible for its own envelope/digest/effect checks. The B helper is an *optional injected callback*, not something A has already accepted or installed.

## Residual hostile challenge

> Even if B returns a well-formed V1 PASS, an A port that trusts an arbitrary callback cannot verify it was computed for the *present candidate*. A returns B_PASS for a structurally correct but stale cached PASS supplied by a dishonest callback. This is expected given the current transport contract, and source-only tests cannot establish honest issuer-bound review. A future versioned binding should include authenticated request/candidate digest and current correction epoch, verified by a separate host authority, before claiming production capability.

This test uses fictional text and a known synthetic fixture key. No model, provider, local Lappy master, private conversation, password, runtime, release, autonomous action or effect authorization is involved. Retain the known FAIL/UNKNOWN semantics; do not force PASS or broaden A's delivery permissions.
## New A PR #13 source subject (2026-11-18)

The A PR subsequently advanced from a6b0405cd1ee9f83ea8c25798a9b9cd605518c8b to 4b3d13e90665b03e0b36d6295de4b7ed23cd4a06 to add a separate **offline MCP synthetic protocol probe**. The exact A midflight_b_bridge.py Git blob remained 695d83e98016ba9a2da7f5051c13bf4a41427a24. The opt-in test accepts only these two pinned immutable source subjects and still verifies the exact bridge blob before execution. New A head's own Lappy Python 3.12 test suite passed 75/75 separately. No live MCP connection or actual ChatGPT interception is qualified.
