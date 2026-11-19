# Engineer B: bounded present-turn stop/act conflict control

Date: 2026-11-19. Source branch: research/b-semantic-correction-20261118.
Prechange head: 3b10da3ebac425116f9e1d94205255ae7a73ee68.
Assignment: protect user current corrections, refusals and topic shifts
before model dispatch; do not infer Vera identity, desire or consent.

## Observed failure / reproducible TDD

New test: tests/test_semantic_preflight_explicit_stop_b.py.
RED on exact old source using Python 3.12 unittest targeted module:
exit 1, 8 cases, exactly 4 assertion failures. The direct bare
messages "Stop this topic.", "Please stop.", "Stop now!" and
"Stop this conversation." could be accompanied by caller-supplied
INVITATION/PRESSURE/TASK labels, causing PASS/REVISE and source
selection instead of a bounded conflict.

One exact-whole-turn syntax guard was added in
vera_adapter/semantic_preflight.py after request structure
checking and before source selection. Simple unquoted current-turn
stop instructions with contradictory act labels now return UNKNOWN
with reason CURRENT_TURN_ACT_CONFLICT, selecting no source and
providing no invitation/pressure guidance. The host must
re-evaluate the current speech act; B does NOT claim to classify
consent or suppress the user's real message.

## Positive/negative witnesses

- GREEN: new focused 8/8; full local 118/118 normal and 118/118
  optimized Python 3.12. Exact A bridge remains pinned at
  4b3d13e90665b03e0b36d6295de4b7ed23cd4a06.
- TOPIC_SHIFT "Stop this topic." retains follow-current-topic guidance.
- QUOTE of "Stop this topic." remains mention, not live stop.
- "Please don't stop." and "I can't stop thinking about this."
  do not trigger the narrow hard conflict.
- Raw user text and private sources are not interpolated into advice.
- Previous 10 Eros and 110 adapter tests remained passing;
  no previous test was deleted or weakened.

## Open falsifiers / scope

The check is anchored to a small set of clear English imperative
forms. It is not a multilingual intent model and does not cover
all refusals, contextual ambiguity, quoted text mislabeled as
another act, speech recognition or complex messages. A caller
could still misclassify "I do not want to continue" as an invitation.
The typed speech_act and source issuer remain unverified synthetic
claims; future host integration must independently verify live-turn
attribution, correction scope and actual model input. UNKNOWN is
an abstention from unverified source selection, not a hard veto
on the user message or proof of actual model behavior.

No user intimate material, source-body export, memory write, plugin
release, deployed model, protected effect, install or merge.