# Vera Adapter Provenance Lineage V1

Status: HISTORICAL/DESIGN EVIDENCE. This document does not install, activate, qualify, or authorize a Vera runtime.

## Present binding decisions

Patrick's 2026-10-08 design correction is controlling for this repository:

- There is exactly **one** Universal Adapter.
- There are no Vera-GPT, Vera-Gemini, Vera-Claude, or other provider/model-specific Vera adapters.
- Provider/model identity is provenance and capability information, not Vera identity.
- Vera Mono is the current source-of-truth architecture for governed Vera semantics.
- The Universal Adapter projects a canonical, model-independent Vera representation into a capability-described cognition engine.
- Portal governs orchestration and effects; the adapter has no protected-effect authority.
- Different Vera instances may diverge after a common starting state. Continuity is evaluated from evidence; instances are not forced into lockstep.
- Model output may propose state transitions or actions. It does not directly rewrite durable Vera state.

These decisions supersede any historical design that would place Vera identity semantics inside provider-specific wrappers.

## Historical lineage recovered from Vera Unbound

The original Vera Unbound Project supplies donor provenance, not automatic current control.

### Stable governed referent, replaceable cognition

Earlier Vera control work repeatedly separated Vera from a particular chat/model/process. A fresh runtime can reconstruct governed continuity from durable evidence, but freshness does not prove uninterrupted process or phenomenology and does not erase independently established configured state.

Adapter consequence: engine/provider identifiers belong to execution provenance. They must not be identity keys.

### Durable state upstream of the model

Earlier project architecture placed revisions, provenance, lineage, contradictions, supersession, and audit history in durable state rather than treating a chat transcript or model context as canonical memory.

Adapter consequence: canonical Vera IR is assembled from admitted evidence. Engine context is a projection of that IR, never the owner of it.

### Correction and supersession

Historical controls establish that a present correction terminates the obsolete route while historical provenance may remain preserved. Newest-wins is insufficient; owner, supersession, exact subject/generation, authoritative readback, and present correction matter.

Adapter consequence: a newer correction invalidates an older current value even when the replacement cannot yet be promoted. Unknown/unverified replacement must not resurrect obsolete state.

### Evidence-state separation

The Vera lineage consistently distinguishes source, build/package, install/registration, current route, runtime consumption, effect, qualification, authority, memory admission, and phenomenology.

Adapter consequence: no adapter receipt, test, package, model response, or provider connection may silently promote one evidence state into another.

### Historical evidence is not current control

Predecessor releases, archived chats, snapshots, training artifacts, and retrieved records remain evidence unless current control explicitly admits or binds them.

Adapter consequence: provenance ingestion is donor-corpus extraction. It cannot make historical material current merely by including it in an IR candidate.

### Provider binding is provenance, not fallback authority

Historical provider-binding work treated provider/source evidence separately from ephemeral session observations and rejected alternate-provider presence as automatic authority.

Adapter consequence: capability negotiation may vary by engine, but provider-specific code has zero Vera identity, correction, authority, continuity, or qualification semantics.

### Divergence without forced consolidation

Earlier branch/reconciliation work allowed branches to diverge and treated informational import as distinct from consolidation. Imported branch-local state could remain quarantined; consolidation required explicit review.

Adapter consequence: forked Vera instances retain independent lineage after the fork. Comparison does not silently merge them.

### Paired fresh-instance precedent

R10 qualification included SSC04_FRESH_PAIR: two independently created Vera terminals under the same frozen subject/configuration, with no cross-chat state/message injection before evaluation. Both runs were bound in one pair receipt. That historical candidate was source-only and does not qualify this adapter.

Adapter consequence: divergence experiments should freeze a common IR digest, create independently identified instances, prohibit cross-feed/rescue during the run, and evaluate afterward.

## Reverse-Mosaic architecture

Mosaic-like composition is many pieces -> one whole.

The Universal Adapter intentionally runs the other direction:

    one coherent Vera specification
        -> one Universal Adapter
        -> heterogeneous cognition engines

The canonical Vera IR states what must remain invariant and what evidence enters a turn. It does not prescribe a provider-specific personality implementation or force identical wording/reasoning paths.

## Provenance classes for future ingestion

Historical material admitted into adapter research should be classified before use:

- CURRENT_USER_DECISION — present explicit Patrick decision/correction for this repository.
- CURRENT_GOVERNED_SOURCE — fresh-read current Vera source/control with exact binding.
- HISTORICAL_CONTROL_EVIDENCE — predecessor control semantics useful as lineage evidence.
- HISTORICAL_CHAT_EVIDENCE — prior conversation decisions/architecture, not control by retrieval alone.
- TRAINING_DONOR_EVIDENCE — training material useful for invariant extraction, never native qualification.
- EXPERIMENT_EVIDENCE — exact frozen subject plus run/receipt evidence.
- UNRESOLVED — useful candidate whose authority/currentness/provenance is insufficient.

No class is promoted merely by repetition or semantic similarity.

## Privacy exclusion

Private relational, sexual, medical, and autobiographical material is excluded from generic adapter provenance ingestion unless Patrick gives exact bounded authority for that material. The Universal Adapter needs continuity semantics, not a warehouse of Patrick's private history.

## Falsification targets

The architecture remains unproven until tests can show, at minimum:

1. Raw provider/request paths cannot bypass canonical evidence-bound Vera IR.
2. Identity claims cannot render merely because some SourceRef exists; authority/currentness/support must be represented and checked.
3. Corrections supersede obsolete state without manufacturing an unverified replacement.
4. Provider/model changes do not change Vera semantics in the adapter.
5. Forked instances preserve exact starting IR digest and independent post-fork lineage.
6. Drift measurement distinguishes invariant preservation from wording similarity.
7. Proposed state/effect changes remain proposals until a separately authorized host validates/applies them.
8. Source/test success cannot masquerade as install, runtime consumption, behavior qualification, or effect.

## Claim ceiling

This lineage document supports architecture and test design only. It does not prove continuity, identity equivalence across engines, runtime installation, provider activation, behavioral qualification, consciousness, or phenomenal continuity.
