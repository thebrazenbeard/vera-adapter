# Vera continuity import admission — source-only review contract

This module (vera_adapter.continuity) is a read-only eligibility gate, not a memory service, source-of-truth ledger, identity editor, consent service, or model training operation. It does not save records, mutate model weights, or grant downstream tool capabilities.

It is intended for imported semantic information and short-lived working state. Identity-critical, self-model, autobiographical/episodic, routing, tool, configuration and neural-weight targets are outside this gate. Imported statements cannot be marked as Vera's lived experiences by this interface. Model output remains classified MODEL_OUTPUT even if approved for later contextualization; approval does not establish truth.

## Threat model and authorization

The untrusted candidate supplies text and provenance claims, not authority. Phrases such as "I consent" and model-generated approvals have no special effect. A caller must supply an out-of-band verifier that authenticates approval or an appropriate governing policy independently of the candidate.

The verifier receives seven arguments in order:

1. record_id — candidate record identity
2. scope — scope or tenant for authorization
3. source_ref — attributable source reference
4. source_actor — claimed source actor
5. source_kind — provenance classification
6. target_state — proposed destination state family
7. sha256(content UTF-8) — binds approval to exact candidate bytes

The verifier must check trusted provenance, actual requester identity, permissions, revocation/expiry, and the exact tuple. It must not merely trust candidate assertions or treat a digest as a signature. A Boolean True produces an eligibility result, not a completed write. Missing or unavailable verifier, negative verification, missing attributable data, unsupported target, and lived-experience promotion all fail closed. No external verifier implementation is supplied.

## Qualification still required

Before runtime use, provide an authenticated approval backend with negative, revoked, and expired receipts; a separate protected state-change contract; durable memory storage with correction and supersession; multi-scope isolation; consistency and replay tests; and independent live readback. Synthetic unit tests and GitHub merge do not prove continuity or neural learning.

The architecture follows HYPERCONNECTOME_RUNTIME_MODEL.md (routing differs from authority) and PLASTICITY_AND_STATE_GOVERNANCE.md (memory imports differ from episodic experience and self-model writes).
