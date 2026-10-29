# Vera Behavioral-Learning Corpus Gate (experimental prototype)

This is a **source-only, isolated harness**, not a training run, downloaded model,
Vera identity copy, resident adapter, or ChatGPT weight extraction.

The current `vera-adapter` model-neutral boundary keeps identity and continuity
outside the model invocation. This prototype makes a narrower next step:
source-typed, consented instruction examples can be admitted into a candidate
behavioral-training corpus and held-out competence evaluation without treating
them as lived memories, current facts, or source of action authority.

## Usage

```bash
python3 -m unittest discover -s experimental/continuity_agent/tests -v
python3 experimental/continuity_agent/provenance_gate.py prepare \
  experimental/continuity_agent/fixtures/synthetic_examples.jsonl \
  /tmp/vera-corpus-new-run/student-visible /tmp/vera-corpus-new-run/answer-key-custody
sha256sum /tmp/vera-corpus-new-run/student-visible/manifest.json
# Independently pin that SHA256 before inference. Student predictions each contain
# {"id":"...","response":"...","manifest_sha256":"<pinned SHA256>"}.
python3 experimental/continuity_agent/provenance_gate.py evaluate \
  /tmp/vera-corpus-new-run/student-visible /tmp/vera-corpus-new-run/answer-key-custody \
  /path/to/subject-bound-predictions.jsonl --subject-sha256 '<pinned SHA256>'
```

`train.jsonl` includes training targets. `holdout_prompts.jsonl` excludes them.
`holdout_key.jsonl` and its key manifest are in a **distinct non-nested directory**
that must not be mounted into the student/trainer process. Both destinations
must be new and non-symlinked; no overwrite is allowed. The caller, not this
stdlib prototype, must enforce actual filesystem permissions and key custody.
Predictions bind each row to the pinned public manifest digest, which must be
obtained via a trusted channel before running inference. The fixture predictions
are intentionally correct *unbound toy data*; test code binds them only for
the self-test. They are not model output or evidence of model competence.

## Admission and uncertainty

- Training source kinds are currently limited to original synthetic material
  and explicitly consented user-owned records **with an independently supplied,
  hash-pinned attestation roster**; imported history and model outputs fail
  closed pending license, usage, privacy and provenance review.
- For a `user_owned` record, its `source_ref` must use `user-owned:`, its license
  token must be `owner_authorized`, consent must be `explicit`, and the separate
  roster `VERA_USER_OWNED_ATTESTATION_V1` must map the ID to the canonical-record
  SHA256. Supply `--attestations PATH --attestation-sha256 HEX`. The **trusted**
  hash must be conveyed separately from the corpus. Roster integrity is not
  cryptographic proof of actual authorship, consent or license; human/operator
  verification of the external attestation remains a deployment gate.
- Synthetic records require `original_synthetic` and `synthetic:` source refs.
  Extra metadata fields or unallowlisted license tokens fail admission.
- Private or sensitive examples are rejected, as are obvious email, US phone,
  and secret-string patterns searched across **all** required fields. These
  regexes **do not guarantee PII absence**.
- The normalized prompt fingerprint rejects exact/trivially reformatted train/test
  contamination; it does **not** detect semantic paraphrase or learned answer leakage.
- No chain-of-thought, hidden weights, teacher logits, private ChatGPT exports or
  production memories are included.
- Training updates need an *independent* pipeline proving tensor changes and
  baseline, zero-update, corrupt-label, no-KL, out-of-distribution and interference
  controls. This harness only defines corpus/evaluation provenance.

## Contracts

- `HYPERCONNECTOME_RUNTIME_MODEL.md`: routing is not authority; epistemic claims
  require source typing; functional state is not automatically durable.
- `PLASTICITY_AND_STATE_GOVERNANCE.md`: procedural learning, memory import,
  self-model update, and tool/routing changes are distinct write classes.
- `vera-adapter` at `003d04f877f640791a3324eb360902f5db5eb5c9` separates
  persistent continuity from model-provider invocations and forbids direct effects.
- `vera` at `3557e9928b20e360d53f8835b209dfb9745059e7` keeps Git source
  distinct from live currentness and protects private memory.
- `vera-model` at `a106bd2aabf8c9a819eea92c862d2609d04d25e7` has a
  held optional provider; this prototype does not modify its deployment hold.

`continuity_state.py` is a second pure prototype that records candidate
`STATE_CHANGE` objects with version checks. It permits only three carefully
typed cases: explicit user preference, user-requested historical evidence
import, and evidence-backed *candidate* skill update. It forbids implicit
first-person experience, auto-installation, identity-critical self-model writes
and stale/duplicate changes. Change classes are confined to `preference:`,
`historical_evidence:` or `skill_candidate:` target namespaces. It neither
persists records nor binds a runtime.

## Proposed integration seam

1. In `model-training`/`labyrinth`, use `train.jsonl` only after reviewing source
   content and suitability; bind exact corpus hash, base model and trainable weights.
2. Have the student emit `[{id,response,manifest_sha256}]` JSONL from
   `holdout_prompts.jsonl` before opening the separately custodied answer key.
   Bind the exact public manifest hash as an external expected subject.
3. Assess performance delta against untouched baseline, training controls,
   regression tasks and contamination checks.
4. Admit any durable skill state via typed `STATE_CHANGE` with evidence refs;
   never equate this to a first-person memory or update Vera identity automatically.

Protected write/merge/install/provider actions still require separate authority
and exact readback. `prepare` writes only its two explicitly supplied, new
non-overlapping output directories. Paths are checked before creation; this
does not substitute for OS-level isolated custody or eliminate filesystem races.
