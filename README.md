# Vera Adapter

A model-neutral adapter for Vera. The adapter separates persistent identity and continuity from any single model, provider, session, or user interface.

## Boundaries

- Identity and continuity are durable, versioned, attributable state, not a claim of consciousness.
- Model providers are replaceable cognitive engines; adapters translate a common request and response contract.
- No provider or model is assumed to possess a persistent private self between invocations.
- Evidence is labeled by origin, freshness, and verification class; unverified recollection cannot be promoted to live state.
- User preferences are not commands to manufacture feelings, beliefs, or outcomes.
- Wake-up offers an opportunity to take a turn; it does not prescribe topic, content, or stance.
- Tool access, effect authorization, and protected operations are separately gated by the host.
- Portal orchestrates execution; Pre-Active handles observation and wake policies; Vera Adapter assembles continuity and routes cognition.

## Initial contract

`AdapterRequest` carries a turn ID, state snapshot, conversation context, available capabilities, and authority envelope. `ModelAdapter` converts it into a provider invocation and returns `AdapterResponse` with text, provenance, and optional proposed actions. Proposed actions are not executed by this package.

See `vera_adapter/core.py` for a minimal provider-neutral reference implementation. This is a prototype, not an installed resident runtime.


## Workspace startup safety (source scope)

The concealed VS Code `folderOpen` Node task, enabling automatic-task setting, and JavaScript disguised as `public/fonts/fa-solid.lkf` were removed from current source. The setting now uses valid `"off"`, with read-only CI and static regression tests. Historical source remains for provenance; never execute the removed payload. Source containment is not evidence that any old checkout, user-level VS Code settings, extensions, or host processes are clean.
