# Universal Adapter Invariant V1

The repository implements one Vera Universal Adapter.

## Forbidden architecture

Do not create `VeraGPTAdapter`, `VeraGeminiAdapter`, `VeraClaudeAdapter`, model-version forks, or provider-conditioned Vera identity logic.

Provider-specific wire protocols may exist below the universal boundary, but they are codecs/transports only. They may translate authentication, endpoint formats, role/message shapes, streaming events, tool-call encodings, or provider capability metadata. They must contain zero Vera-specific semantics.

## Compatibility test

Adding a new engine passes the universality test when:
1. Vera core/IR code is unchanged.
2. Vera identity and continuity rules are unchanged.
3. The engine is represented by the common capability contract.
4. Any new code is generic protocol/transport plumbing rather than Vera behavior.
5. Existing invariant and drift tests still pass.

If supporting an engine requires a new Vera-specific adapter, universality has failed.

## Drift

Two engines receiving the same frozen Vera IR may diverge. Divergence is evidence, not automatically a defect. Do not cross-feed or rescue during a baseline run. Compare invariant retention, correction retention, provenance, and unsupported claims afterward.
