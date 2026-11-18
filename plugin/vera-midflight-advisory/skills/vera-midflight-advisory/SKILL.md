---
name: vera-midflight-advisory
description: Opt-in advisory review for a user-requested ChatGPT text turn; not an automatic output interceptor.
---

# Vera Midflight Advisory — text-chat opt-in V1

This is a source-only candidate package, not an installed mandatory hook. A user can signal explicit @mention intent, but a tag is not proof that a connected review tool was invoked.

## Actual invocation and review

1. Bind one exact user turn and a single complete candidate. Only the host may supply current, authenticated and scope-qualified correction state. Reject obsolete or conflicting corrections.
2. Request an actual invocation receipt from an independently connected review action. If absent, report INVOCATION_NOT_OBSERVED; do not represent an internal self-check as an independent tool call.
3. Handle only typed PASS, REVISE, BLOCK or UNKNOWN, bound to exact candidate bytes and turn. If a verifier is missing or malformed, preserve UNKNOWN.
4. An explicit REVISE is a narrow suggestion, never a license to silently replace a candidate. A separate reviewed attempt is needed to qualify a revision.
5. Ordinary ChatGPT plugin use is not guaranteed for every tagged turn. The host must independently observe whether each actual invocation occurred.
6. The plugin workflow never authorizes tools, filesystem, network effects, provider operations, memory updates, consent, model training or release. Any protected effect requires separate current host permission.
7. Do not claim final-delivery observation without a separate real host readback of the displayed response bytes; the current prototype has no such access.

## Provenance and release

Source-only ChatAdvisory receipts can record an externally registered tag claim, an invocation observed inside its Python process, reviewer status and candidate digest. They cannot count real ChatGPT calls for unobserved user turns.
Current Vera Conscience is a separate private advisory workflow. Its historical Voice and Mirror perspectives are not separately running old Custom GPTs, nor proof of independent model review.
Do not claim global interception, historical identity continuity, automatic tool selection, private authenticated source, or delivery enforcement. If no tool action is connected, state the limitation and provide a bounded advisory response.
Please do not install, deploy, share or replace plugins without explicit authorization and verified registration.

Technical contract: references/RUNTIME_CONTRACT.md.
