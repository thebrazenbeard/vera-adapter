# Vera Adapter — provider-neutral invocation contracts

**A small Python reference package for describing an AI turn and checking basic response correlation.**

Vera Adapter exposes typed request and response records, a provider-adapter interface, and a validator. Applications can use these shapes when connecting different model providers to a shared conversation host. The package is **an API prototype**, not a hosted provider gateway, installed resident agent, persistent identity system, or authorization service.

The name reflects its origin in the Vera ecosystem; the Python contract itself does not require a particular model vendor. Actual provider integrations are left to applications implementing `ModelAdapter`.

## Implemented API

| Export | Purpose | Boundary |
| --- | --- | --- |
| `AdapterRequest` | Holds a turn ID plus caller-supplied identity labels, continuity and conversation tuples, capability names, and authority strings | These fields are data supplied by the caller, **not** verified credentials or durable state |
| `AdapterResponse` | Holds the corresponding turn ID, model-produced text, provider/model labels, and proposed-action strings | Provider/model labels are not cryptographically authenticated; proposals are not executed |
| `ModelAdapter` | Python `Protocol` declaring `invoke(request) -> AdapterResponse` | No concrete API client, model selection, transport, or retry logic is included |
| `validate_response` | Checks that the request turn ID is nonempty and matches the response, and that provider/model labels are nonempty | Does not validate the response's content, authorization, provenance truthfulness, or effect permissions |

The public exports are defined in [`vera_adapter/__init__.py`](vera_adapter/__init__.py) and implemented in [`vera_adapter/core.py`](vera_adapter/core.py). The request and response records are frozen dataclasses, but their contents are **not deep-frozen**: for example, a mutable mapping passed as `identity` remains mutable. The design must not be used as an immutable host authority binding.

## Try the reference contract

The source package uses the Python standard library; no installation or external model account is needed to run this self-contained example from the repository root:

```python
from vera_adapter import AdapterRequest, AdapterResponse, validate_response

request = AdapterRequest(
    turn_id="turn-001",
    identity={"agent": "example"},
    continuity=(),
    conversation=("Hello",),
)

# A test response, not a live provider invocation.
response = AdapterResponse(
    turn_id="turn-001",
    text="Hello back.",
    provider="example-provider",
    model="example-model",
)

checked = validate_response(request, response)
print(checked.text)  # Hello back.
```

`validate_response` raises `ValueError` when the turn IDs differ, the request turn ID is empty, or either the provider or model string is empty. A successful call means those **structural checks** passed. It does not mean that the named provider actually generated the response.

To connect a real model, an application must implement `ModelAdapter.invoke`, obtain provider authentication and provenance from its own trusted runtime, and authorize any requested side effects through a separate host-owned enforcement boundary. Supplying strings in the `authority` or `capabilities` fields cannot grant those rights.

## Run the tests

From the repository root:

```bash
python3 -B -m unittest discover -s tests -v
```

[`tests/test_core.py`](tests/test_core.py) checks matching and mismatching turn IDs. [`tests/test_workspace_startup_safety.py`](tests/test_workspace_startup_safety.py) checks that the **tracked source tree** does not enable hidden VS Code workspace-startup execution. The [GitHub Actions workflow](.github/workflows/workspace-startup-safety.yml) runs only that workspace-safety subset; a green workflow is not full API, provider, or host validation.

## Security and continuity limits

- The package does **not** persist or authenticate identity, continuity, memory, consent, provider identity, or user permissions. It has no cryptographic signatures, replay-resistant authority leases, or authorization decision service.
- An `AdapterResponse` may include `proposed_actions`, but this package provides no executor. Applications must classify and authorize effects independently before execution.
- Caller-supplied identity, authority, capability, provider, and model names are descriptions only; no trusted host injection or immutable binding is implemented here.
- The historical concealed editor-startup task and disguised pseudo-font executable were removed from current tracked source. The source safety tests do not establish that any earlier checkout, editor extension, or workstation was clean.

## License and assets

**No root `LICENSE` or `COPYING` file is tracked at this revision.** Public visibility does not by itself grant redistribution, derivative-work, or commercial-use permission. Confirm the rights applicable to your use before repackaging this repository. The legacy [`public/fonts/`](public/fonts/README.md) directory is not part of the adapter API; its own documentation describes a different application and does not establish reusable font-asset rights.

For implementation details and scope, start with the [core contract](vera_adapter/core.py), the [API tests](tests/test_core.py), and the [source-safety tests](tests/test_workspace_startup_safety.py).
