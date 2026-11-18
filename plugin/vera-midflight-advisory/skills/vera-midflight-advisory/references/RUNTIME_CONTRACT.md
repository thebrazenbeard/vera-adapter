# Vera Midflight Advisory — source-only runtime contract

Versioned receipt: VERA_CHAT_ADVISORY_V1. Separate buffered host review: VERA_MIDFLIGHT_HOST_GATE_V1.

Reproduce from repository root with Python 3.12+ at the reviewed commit:

    python -B -m unittest discover -s tests -p "test_*.py" -v
    python -B -m examples.midflight_synthetic_demo

ChatAdvisory.registered intent is a host-supplied claim. An actual invocation receipt requires the review function to be entered. A typed review result does not prove the assistant applied its suggestion or that ChatGPT showed the reviewed output.

NO NATIVE INTERCEPTION. Ordinary ChatGPT tool selection cannot guarantee plugin invocation, prevent earlier streaming output, or observe every user turn. Only a host-controlled proxy/sink can gate actual delivery and effects.

The user may explicitly opt in by @mentioning a connected reviewer in each text-chat turn, but a mention without a call is recorded as MISSED only when an external trusted harness actually observed that turn.

Never include private candidate text, full sensitive prompts, credentials, or private memory in a public receipt. Proposed actions are never authorized by review.

Engineer B owns semantics; A owns the host surface. Separate verified correction lifecycle belongs to F.U.C.K.U.P.; regression admission belongs to DriftGuard. Real host identity, app registration, B source integration and final client delivery require independent qualification.
