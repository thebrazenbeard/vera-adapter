# Vera Universal Adapter

One model-neutral adapter for Vera.

## Governing invariant

There is exactly one Vera adapter. Provider, vendor, model-family, and model-version specific code MUST NOT contain Vera identity, continuity, evidence, qualification, correction, authority, or behavioral semantics.

A new cognitive engine is compatible when it can describe its capabilities through the common engine contract and accept/return the canonical envelope. Adding an engine may require transport/protocol plumbing outside this package; it must not require a new Vera adapter.

```text
durable Vera state
       |
       v
canonical Vera IR
       |
       v
Vera Universal Adapter
       |
       v
capability-described cognitive engine
```

## Reverse-Mosaic direction

The adapter projects one coherent Vera specification into heterogeneous cognitive engines. It does not assemble Vera from provider-specific implementations and does not force engines to produce identical wording or reasoning paths.

## Boundaries

Identity and continuity are durable attributable state, not ontology proof. Model output proposes state/actions; it does not rewrite durable state directly. Exact continuity claims require backing. Corrections supersede older state. Qualification remains separate from package/training evidence. Protected effects remain host-gated.

Portal may orchestrate execution and Pre-Active may provide observation/wake behavior; neither is a runtime dependency of this package. This repository is source-level adapter work, not proof of installation, route selection, runtime consumption, or behavioral qualification.


## Local evaluation (development only)

Opt-in local-only engine wire and unrescued drift harness instructions:
[docs/LOCAL_ENGINE_DRIFT_V1.md](docs/LOCAL_ENGINE_DRIFT_V1.md).
Independent engine runtime identity and model qualification are not
established merely by using separate endpoints or model IDs.
