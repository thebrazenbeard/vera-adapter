# Historical ChatGPT import quarantine — source-only V1

This module accepts *normalized claim candidates* produced by a separate,
private ChatGPT export parser. It does not open ZIP archives, select claims,
tag topics, keep plaintext on disk, call a model, or modify durable memory.
The owner-scoped importer must first authenticate the source archive and its
conversation/message records. A successful archive import is not a memory
admission or a current-fact verification.

This is a **Vera Adapter preflight boundary**, not a competing memory-lifecycle
coordinator. `MemoryLedger`'s draft lifecycle planner owns proposals such as
review-current, review-historical, review-correction, hold and expire; Vera
Mono owns current governed-memory writes; `deepmemorystorage` is historical
evidence, not current authority or a public private-transcript destination.
The adapter's defensive flags are not a replacement for those contracts, and
no live dependency on their unmerged draft branches is introduced here.

## Input contract

`HistoryEvidence` contains:

| Field | Meaning | Trust |
| --- | --- | --- |
| `record_id` | Unique candidate identity within one staging batch | Caller-allocated, validated for uniqueness |
| `export_fingerprint` | Lowercase SHA-256 hex of the authenticated source ZIP | Claimed by upstream, not rehashed here |
| `conversation_id`, `message_id` | Original source identifiers | Historical data; nonblank |
| `role` | `user`, `assistant`, or `tool` | Historical author label; not host authority |
| `occurred_at` | Offset-aware ISO-8601 source timestamp or `None` | Historical; no freshness claim |
| `claim_key` | Optional upstream comparison key | Heuristic, not semantic equivalence |
| `claim_text` | Private candidate claim text | Untrusted historical content |
| `correction_of` | Optional prior candidate record ID | Claimed link; never self-executing |

The trusted caller supplies `scope` separately; archived content cannot choose
its owner. The stage function returns immutable `StagedHistoryClaim` instances
with `QUARANTINED` status and `HISTORICAL_UNTRUSTED` flag. Each source reference
is derived from the archive fingerprint and escaped conversation/message IDs.

Assistant-produced statements remain `MODEL_OUTPUT`; tool messages remain
`EXTERNAL_SOURCE`; only a historical human user message is `USER_SUPPLIED`.
None of those labels independently verifies a proposition. Missing or naive
timestamps are never silently interpreted as current; absent timestamps are
flagged `TIMESTAMP_UNKNOWN`.

## Conflict and correction handling

- Multiple different texts with a matching `claim_key` become
  `VALUE_VARIANTS_REVIEW`, not an automatic contradiction verdict. Older
  timestamped variants receive `OLDER_HISTORICAL_VARIANT`, not an automatic
  assertion that the newest one is true.
- A `correction_of` pointer is checked for existence in the same batch and
  export and for cycles. The original candidate remains intact. The claimed
  correction receives `HISTORICAL_CORRECTION_UNVERIFIED`; reversed timestamps
  and cross-role corrections get additional flags.
- The current API deliberately refuses eligibility for historical corrections
  or unresolved variants. Resolution needs a separate trusted correction and
  admission contract, with a traceable decision and supersession record.
- A correction target outside the current staging batch is rejected rather
  than silently resolved against ambient/live memory. An upstream merger can
  construct a complete batch before staging.

## Admission boundary

`inspect_history_admission(staged, verifier=None)` is *read-only*. For an
otherwise unambiguous candidate it delegates to the `continuity` gate's
host-supplied authorization verifier, bound to record ID, owner scope, source
reference, source role/class, target `semantic_memory`, and SHA-256 of the
exact UTF-8 claim text. Without this independent verifier it fails closed.

Even `ELIGIBLE_FOR_DOWNSTREAM_REVIEW_ONLY` is **not** a memory write, a
current-truth assertion, a lived experience, a model-weight update, consent,
or permission to change identity. Any durable write requires a separately
protected `memory import` state-change record with prior/successor version,
evidence, authority, time, reversibility, and readback. Historical user
statements cannot authorize themselves by saying "I consent".

## Security and qualification limits

The staging API is a pure in-memory normalization aid for trusted callers.
It is not an authenticated network boundary: a caller must protect its scope,
vault, key custody, and output. Source references and claim text are private,
and must not be placed in public repository comments, CI logs, or issue bodies.

Synthetic tests cover duplicate IDs, source roles, age/unknown timestamps,
ambiguous values, correction links/cycles, content-supplied consent, and
external-verifier binding. Real account-wide candidate extraction, encrypted
storage, cross-batch deduplication, trusted current review, owner pairing,
backup recovery, and selected-model retrieval remain separate gates.

This is consistent with `PLASTICITY_AND_STATE_GOVERNANCE.md`: imported
knowledge, lived episodes, and identity-critical state are different write
classes; a proposed update does not confer its own write authority.
