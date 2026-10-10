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
    if (type(request.turn_id) is not str or not request.turn_id.strip()
            or type(response.turn_id) is not str
            or response.turn_id != request.turn_id):
        raise ValueError("turn identity mismatch")
    if (type(response.provider) is not str or not response.provider.strip()
            or type(response.model) is not str or not response.model.strip()):
        raise ValueError("missing model provenance")
    return response
