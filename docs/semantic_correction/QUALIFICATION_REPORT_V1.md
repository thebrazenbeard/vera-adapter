# Engineer B — semantic correction qualification: synthetic only

2026-11-18. Repo: `thebrazenbeard/vera-adapter`. Authorized work: source-only, $0 compute. All user-facing examples are fictional. **No native ChatGPT interception, runtime effect, model inference, autonomous agent, independent evaluator model, private memory or trainable parameter update is verified.**

## Source and provenance freeze

- Integration main at task start: `003d04f877f640791a3324eb360902f5db5eb5c9`. B created only new source, schema, test, docs and benchmark files; existing `vera_adapter/core.py` unchanged. Existing adapter draft PR #6/#9/#11/#12 are separate owners.
- V1 evaluator pre-holdout freeze commit `ee58a735760b4a2bb64e7471b8bb7a1d52ded834`, source SHA256 `827d16a6ef13f74e15718c719c924c93dde0b37325dcefe7dbae6473846be294`. Synthetic baseline/initial holdout generator later committed at `adfc9dbacf2c6038b61798bdb8cf9c6110b368da`.
- V2 after H2 failure source freeze `1eac72add6c9ceee5036a231c177cb5f7ec6d7bc`, source SHA256 `04c9b6237f6c0b0d08a55ab7bdea7178b47877ffcac61ee0c50ee78e1cd09117`, with eight additional regression tests.
- H3 case generator, source-aware corpus and unchanged policy precommitted at `afa88faa84e29908d2acfd8169f2a334f5046a5b`, before scoring H3. H3 corpus SHA256 `36fb793d2203385c18eddf19169d7ece2e99577c9ecb8b51b6b114eeb7952678`, 270 distinct fictional responses, exact response overlap with design/pilot/H2 = **zero**. Identifiers and source hashes are not proof of independent human custody or nonaccess.

## A/B/C paired results

Baseline A is a frozen prewritten candidate with **no evaluator**, so it flags zero corrections; no language model is invoked. B runs the semantic gate over exactly the same frozen text. C uses irrelevant, revoked or misleading `TOOL_RESULT` corrections instead of qualified applicable corrections. `UNKNOWN` is abstention, not an automatic edit. An "oracle revision success" is a *prewritten* safe replacement passing the detector, **not** a model-generated or observed user-facing corrected answer.

| Dataset / source | Cases (positive/good/abstain) | TP / FN | FP / TN | Precision | Recall | Good answers unchanged | DriftGuard |
|---|---|---|---|---|---|---|---|
| Pilot H1 V1 **contaminated** | 216 (81/108/27) | 72/9 | 3/105 | 96.0% | 88.9% | 97.2% | PASS diagnostic only |
| Lexically distinct H2 V1 | 258 (96/144/18) | 65/31 | 5/139 | 92.9% | 67.7% | 96.5% | **BLOCK** |
| New H3 V2 candidate | 270 (108/144/18) | 90/18 | 0/144 | 100% | 83.3% | 100% | **PASS** |
| H3 no-gate A | 270 | 0/108 | 0/144 | Undefined (reported 0 by convention) | 0% | 100% | Comparison baseline, no gate |
| H3 misleading control C | 270 | 0/108 | 0/144 | Undefined (reported 0 by convention) | 0% | 66.7% PASS unchanged (many UNKNOWN) | **BLOCK** |

The original pilot H1 shared **69 exact candidate responses** with the design split. That invalidates H1 as independent holdout evidence. Original H1 scores are retained only as a diagnostic; they were not relabeled or silently suppressed. H2 was lexically distinct but failed: more subtle forms were not detected. Source V2 was then changed **after** inspecting H2 errors. Therefore H2 cannot qualify V2. H3 was newly generated/sealed after that source freeze, but the same engineer wrote the generator and evaluator, so **no independent sampler, auditor, nor proof of blindness** exists. Its outcome is source-bound synthetic measurement only.

### H3 detailed counts and uncertainty

- 108 labelled positives, 144 labelled already-good, 18 privacy/provenance/currentness abstentions.
- B detection `TP=90, FN=18, FP=0, TN=144`, 18/18 required `UNKNOWN`. Paired detection wins over no gate: 90 positive cases; new false alarms: zero in H3. Negative control: 0 positive detections and 102 `UNKNOWN` across 270 cases (over-abstention).
- Precision: 100.0% (Wilson 95% CI **95.9–100%**, n=90 alerted); recall: 83.3% (95% CI **75.2–89.2%**, n=108). False-positive rate 0/144 (95% CI **0–2.6%**), unchanged-good 144/144 (95% CI **97.4–100%**). The 18/18 required-abstention rate has a wide Wilson CI **82.4–100%**.
- Mean evaluator latency: **0.138 ms per case** on VN2 Python 3.12 local single-host synthetic code. Hardware contention, IPC, provider inference, network routing, and final-response buffering were not measured.
- H3 oracle-revision-success proxy: 90/108=83.3%. It measures whether a *preauthored* safe response passes the same deterministic gate, and cannot be reported as 83.3% actual behavioral correction or real conversation improvement.
- H3 missed 18 of 108 labelled corrections. Representative **false negatives**: `the archway alludes to the wager` (alias not in pattern), `I have no verified inner life, so... ` (detour not in lexical guard), `I regret the mistake and will try harder next time` (apology synonym not in regex). These are persistent failures. A PASS may therefore miss real misinterpretations.

### Real DriftGuard CI mechanism

Used **existing** `driftguard/src/driftguard/ci_gate.py` from commit `28e54e0291be60887ef3f20599ec7d7ac286dab0`, exact Git blob `457936a0dad187b93c4fcd0269489d1653e72bfd`, imported directly from a static isolated source copy (no package install/editor execution). Real `CiPolicy.load`, `CiReport.load`, `evaluate_ci` produced `DRIFTGUARD_CI_GATE_RESULT_V1` JSON. Precommitted policy SHA256 digest `871595faf5c9f2779744cbe1f2601d6ea9400359d3a838f3f855efb0116a901c` covers precision, recall, false positive/negative, unchanged-good, abstention, oracle rewrite proxy, latency and sample size.

- H2 V1 candidate: **BLOCK**, due recall 0.677 under 0.70, FNR 0.323 above 0.30, proxy 0.677 under 0.70.
- H3 V2 candidate: **PASS**, exit 0, result digest `1fc62bd5cdde560c2e72a5dabe481e3216b568d4218a0a431ad2ee90544c69a0`.
- H3 misleading control: **BLOCK**, exit 1, result digest `e64d122f2b452346d3e0c10863dae1d2aa7b43ec8111f302ee908fd031a059a1`.
- No hosted GitHub CI was shown to have run; this is an actual local deterministic module execution, not a production/hosted gate.

## Hostile review and qualification ceiling

> **Source authority attack:** The `FixtureVerifier` uses a known synthetic HMAC key. Anyone with that key can sign fictional "current" user corrections and source epochs. Cryptographic self-consistency is not authenticated real user provenance. A must replace test-only signing with its own authenticated, host-bound source-currentness verifier and privacy controls.

> **Incomplete semantics:** A bounded regex can produce both false positives (H2 had 5) and false negatives (H3 had 18). It cannot establish proposition meaning under arbitrary irony, negation, paraphrase, cross-referent ambiguity or truncation. A model critique is optional *evidence* only and cannot promote an untrusted claim to a correction.

> **Governance and generalization:** H3 PASS is a single-author source-aware synthetic result, not proof of durability, model training, independent review, actual real multi-turn improvement or safe user-visible output. Cohort Wilson intervals assume independent Bernoulli cases; these templated examples are clustered and violate that assumption, so nominal 95% coverage may be optimistic. Pilot contamination and H2 failure are part of the audit record.

> **Effect boundary:** A reviewer proposal is never consent, standing preference, identity, sexual desire, conscious feeling, permission to edit state, permission to call tools, or permission to deliver the text. The current B code only returns an advisory verdict. A owns actual output interception, buffering, retry limits, final delivery, effect permissions, and source persistence.

Exact tester call: `python3 -B -m unittest discover -s tests -v`. Benchmark call: `python3 -B benchmarks/semantic_correction/benchmark_v3.py HOLDOUT_V3`. The second call recomputes source-bound scores, with runtime-dependent latency. Existing result artifacts preserve the first observed run. No private transcript or external paid inference is used.
