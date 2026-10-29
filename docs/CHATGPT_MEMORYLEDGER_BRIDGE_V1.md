# ChatGPT export → MemoryLedger proposal bridge (source candidate)

Status: **source-only**, no live owner broker, memory admission, model context,
DeepMemoryStorage writer or private account processing.

This optional module joins two unmerged, separately reviewed source candidates:

- `thebrazenbeard/stm` account-export PR #3 at
  `f9cb7fe84dce07fba7cab5dda2dda3c3cb33ce0a` (`chatgpt_graph.HistoricalNode`);
- `thebrazenbeard/MemoryLedger` PR #1 at
  `e1b62d0552d32262e37d127e7e9c386f541c2e4a`
  (`ConversationEvent`, `LifecyclePlanner`, immutable contracts).

The adapter itself owns neither source authentication nor lifecycle policy.
`propose_historical_review` requires a host-owned `resolve_source` callback
and an independent `authorize` callback. Those callbacks must verify the
archive record, current principal, original speaker, third-party scope,
metadata and consent in a trusted process. Python dataclass construction is
**not** authentication. The HMAC locator key must remain private.

## Conversion and guardrails

1. Only an authenticated, individually attributable historical **user** node
   with a real original message ID can enter the candidate seam. Assistant,
   tool, absent-message and unknown-source nodes return `HOLD`.
2. The host must supply exact tenant, project, identity, privacy scope and a
   verified content digest. Missing project/identity is **not** filled from
   conversation title, current project or model inference.
3. The original node event time must exist and match the host's resolved time.
   Update/retrieval/Git/host clock never substitutes for missing event time.
4. A private HMAC derives stable, bounded event/conversation/source handles
   without emitting original account IDs. These handles require the host's
   confidential resolver for reverse lookup.
5. The bridge refuses `CURRENT_REVIEW` grants for imported account history.
   It requires an explicit historical-review policy with **no STM live-record
   source expiry**. Day-30/day-45 does not retroactively expire the export.
6. Quotes, instructions, hypotheticals and unknown speech acts are held. A
   claimed correction needs a verified exact target and complete scoped
   ancestry; the MemoryLedger planner independently limits ancestry to 64.
7. The only positive result is an in-memory `HistoricalReviewEnvelope` with
   `PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT`. It contains no `memory_id`,
   accepted `ledger_path`, current-truth assertion, consent or model instruction.

No state is written. This adapter must not be used to export content into the
**public** `thebrazenbeard/deepmemorystorage` ledger. A future private DMS-like
destination requires a separately authenticated, encrypted, correction- and
deletion-capable sink with independently read-back receipts.

## Exact-source synthetic verification

In isolated checkouts of the two pinned draft heads and Vera Adapter, run:

```bash
PYTHONPATH=/path/to/vera-adapter:/path/to/stm-pr3:/path/to/memoryledger-pr1 \
  python -m unittest discover -s tests -v
```

`test_history_memoryledger_bridge.py` executes the real STM graph derivation
and real MemoryLedger planner on entirely invented history. It checks correct
historical-only proposal, forged identity/binding, revoked consent,
assistant-versus-owner role, absent/fabricated time, ambiguous classification,
current-review denial, correction ancestry, and no DMS-record fabrication.
The test module is skipped when optional source packages are unavailable; a
normal green adapter suite with that skip is **not** cross-repo qualification.

## Unqualified

- trusted Windows/Android principal and consent binding;
- provenance extraction and host classification on real 1,960 conversations;
- private HMAC key management and source-to-identifier readback;
- complete cross-window correction ancestry and revocation/tombstones;
- independent held-out memory-quality comparison;
- live Vera model retrieval/inference and private DMS acceptance/deletion;
- any current/semantic/identity or neural-weight update.
