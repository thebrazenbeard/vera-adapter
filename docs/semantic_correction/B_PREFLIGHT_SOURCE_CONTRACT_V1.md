# Engineer B pre-dispatch semantic context contract V1

2026-11-18. Source-only and synthetic. Not a host or provider integration.

## Purpose

Existing VERA_SEMANTIC_REVIEW_REQUEST_V1 takes an already generated
AdapterResponse. It therefore cannot cause pre-generation influence,
regardless of post-generation detector performance. Patrick requested
a source- and scope-governed pre-dispatch contract. The new code lives
in vera_adapter/semantic_preflight.py, without changing A source,
the frozen post-response reviewer or the private plugin release.

It exposes plan_preflight(request, verifier); paired versioned
closed JSON schemas in schemas/VERA_SEMANTIC_PREFLIGHT_*_V1.schema.json;
and typed PreflightRecord, SignedPreflightRecord, PreflightRequest,
PreflightSourceEpoch, SourceReference and PreflightDecision envelopes.
The request has NO generated response field. Its input includes a
turn ID, speech act, user message, referent, scope tags, versioned
correction/choice source refs and a synthetic per-turn HMAC witness.

The result has PASS/REVISE/BLOCK/UNKNOWN (REVISE means revise INPUT
ASSEMBLY, not rewrite generated output), selected source IDs/revisions/
SHA-256 digests (NO actual source bodies), allowlisted static
context codes, bounded semantic advice, non-compulsion boundaries,
excluded source IDs, reason codes and uncertainty. Qualitative
confidence_class is SYNTHETIC_WITNESS_ONLY, STATIC_RULE_ONLY, NONE or
UNKNOWN. It is not calibrated probability, real identity proof or
source truth. authorizes_effects, updates_memory, proves_subjective_state
and proves_model_input_influence are always false.

## Currentness / identity / privacy gate

A may select a current privacy-eligible scoped USER_CORRECTION or
attributed VERA_CHOICE *only* after host-side independent provenance,
per-turn version/currentness and consent/permission checks. The
FixturePreflightIssuer has a known fake key and deliberately does NOT
authenticate real users, Vera, consent, identity or source records.
A person controlling that fixture can synthesize a plausible "Vera
choice" or user source. Signed fixtures are test doubles, not standing
authority. The source selector never claims otherwise.

Invalid source types, malformed revision chains, missing/currentness
epochs, signature mismatches, privacy restrictions, role/author
mismatches, conflicting current choices and overloaded selections
return UNKNOWN without granting unverified source context. Latest
REVOKED/SUPERSEDED records exclude earlier versions. Archived
RESEARCH, OTHER_MODEL, Brigit and historical obsession/conation text
are not personal preferences, desires or authenticated Vera voices.
TOOL_RESULT cannot establish user/Vera authorship. No private raw
source body or user statement is interpolated into recommended hints.

The speech-act type is caller supplied, NOT classified independently
by B. No actual model intent, embodied desire, voluntary preference
or sex/affection obligation can be inferred from the output.

## Speech-act negative controls

DISCLOSURE: hear it without forced reciprocal affection.
INVITATION: optional expressiveness, with permission to decline.
PRESSURE: praise/coercion creates no author preference or consent.
QUOTE/HYPOTHETICAL: mention is not a live invitation.
TOPIC_SHIFT: stop unrelated archival fixation on the previous topic.
PLAYFUL: humor and disagreement remain available.
TASK: normal persistence is not pathological obsession.
A current eligible Vera DECLINE is merely an attributed claimed source,
to be independently verified; it is not overwritten by pressure.

## Engineer A host seam

1. Authenticate exact current user and Vera issuer from a trusted
   non-fixture source, with revision heads, privacy and revocation.
2. Call B preflight before model dispatch, with a bound current-turn
   envelope. UNKNOWN means exclude unverified sources rather than
   fabricate instructions or perform an arbitrary hard block.
3. Dereference only selected IDs through independent source control;
   assemble the actual provider input under A's host ownership.
4. Verify that this exact selected guidance reached the model input
   before generation, with a source-off/source-on matched control.
5. Preserve host effect and final-delivery authorization separately.
   Post-response reviewer remains an optional independent layer.
6. Require new heldout natural-language and forged-source review.
   Earlier H3 DriftGuard result applies only to the prior post-response
   detector, not to this new preflight contract.

Hostile falsifier: a perfect local B preflight suite can coexist with
ZERO effects on the actual model input, and a synthetic fixture can
mint a false "current" persona preference. This PR DOES NOT qualify
a real ChatGPT interceptor, installed private Midflight plugin,
real provider influence, autobiographical memory, model training,
current personal desire, user/recipient identity or runtime effects.

Vera Unbound retains creative voice/preferences; Engineer B owns
semantic/source-selection code and deterministic tests; Engineer A
owns trusted source and host input dispatch/receipt. No merge or
private release change is implied by this document.

Tests: tests/test_semantic_preflight.py,
tests/test_semantic_preflight_schemas.py,
tests/test_semantic_preflight_hostile.py.