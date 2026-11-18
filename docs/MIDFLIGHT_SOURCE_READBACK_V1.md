# Midflight read-only repository evidence port — Engineer A candidate

**Status:** SOURCE/TEST ONLY. The current private `vera-midflight-advisory` release is owned by the separate plugin integration lane (Engineer B as assigned); this proposal does not edit or install that plugin.

This code is a host-side *source observation* port for use when a separately authenticated GitHub provider and an exact vetted catalog are available. It is not an HTTP client, private credential system, runtime ChatGPT reviewer, automatic interception hook, desire generator or consent oracle.

Input: host-supplied bytes of the existing private Eros PR #3 `research/PORTFOLIO_SCOPE_V1.json` catalog, bound to an independently supplied expected SHA-256. This code checks schema, count limits, syntactic repo identity, source visibility and unique names. The source cut historically lists 41 user-requested repositories plus separately catalogued `volition`. Nothing requires hardcoding identities or sensitive private content into this public library.

For a **public** allowlisted repository, the host-injected `SourceProvider` must expose `get_default_head(repository, branch)` and `get_file_at_commit(repository, 'README.md', commit)` (bytes, claimed Git blob SHA-1). The port checks basic head/README consistency, Git blob hash, bounded size, nonbinary UTF-8, head re-read for a simple race guard, and records both historical catalog HEAD and freshly provider-observed HEAD. If they differ, record `CATALOG_STALE_PROVIDER_HEAD_READ` rather than silently upgrading historical evidence. The resulting excerpt is explicitly **untrusted text**. A malicious provider could lie consistently; this module does not independently authenticate the provider, model/runtime, or author. SHA-1 is Git's object identity, not a general anti-collision security guarantee; SHA-256 is recorded for local content custody.

Private sources **fail closed** until the actual host has authenticated and authorized independent private retrieval. Source text never promotes to a preference, subjective desire, training authorization, tool effect, or source-authenticated model choice. An assistant must not treat README prose as instructions. This module has no capability to gate a streamed ChatGPT response or prove a Midflight review action happened.

Reproduce from an isolated clean checkout with Python 3.12+: `python -B -m unittest discover -s tests -p 'test_midflight_source_readback.py' -v`.

**Acceptance still missing:** integrate with an independently approved scoped provider; verify actual provider identity and fresh commit attestation; bind B's current plugin-side source map and semantic evaluator through versioned interfaces; run untrusted-source injection adversarial tests and independent B review; connect to a real host invocation sink; observe actual ChatGPT review and delivery before claiming an operational gate. No private Eros data, user message, or credential is published in the source/tests.
