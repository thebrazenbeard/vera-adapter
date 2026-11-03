"""Model-neutral Vera invocation contracts. No tool effects are executed here."""
from dataclasses import dataclass, field
from typing import Protocol, Mapping

@dataclass(frozen=True)
class AdapterRequest:
    turn_id: str
    identity: Mapping[str, str]
    continuity: tuple[str, ...]
    conversation: tuple[str, ...]
    capabilities: tuple[str, ...] = ()
    authority: tuple[str, ...] = ()

@dataclass(frozen=True)
class AdapterResponse:
    turn_id: str
    text: str
    provider: str
    model: str
    proposed_actions: tuple[str, ...] = ()

class ModelAdapter(Protocol):
    def invoke(self, request: AdapterRequest) -> AdapterResponse: ...

def validate_response(request: AdapterRequest, response: AdapterResponse) -> AdapterResponse:
    """Validate envelope shape, not live provider identity or effect authority.

    The model/provider strings are provenance *claims*. A host-owned adapter
    must separately verify installation, registration, execution and receipts.
    """
    if type(request) is not AdapterRequest or type(response) is not AdapterResponse:
        raise TypeError("exact AdapterRequest and AdapterResponse required")
    if (type(request.turn_id) is not str or not request.turn_id.strip()
            or type(response.turn_id) is not str
            or response.turn_id != request.turn_id):
        raise ValueError("turn identity mismatch")
    def visible_provenance(value: object) -> bool:
        # Labels are opaque and provider-neutral, but must be bounded and
        # visibly printable. Unicode control/format characters can make
        # attacker-supplied provenance appear empty or visually misleading.
        return (type(value) is str and 1 <= len(value) <= 1024
                and bool(value.strip()) and value.isprintable())

    if not visible_provenance(response.provider) or not visible_provenance(response.model):
        raise ValueError("missing model provenance")
    if (type(response.text) is not str
            or type(response.proposed_actions) is not tuple
            or any(type(action) is not str or not action.strip()
                   for action in response.proposed_actions)):
        raise ValueError("invalid response envelope")
    return response
