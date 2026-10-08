"""Model-neutral Vera invocation contracts. No tool effects are executed here."""
from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .ir import VeraIR

@dataclass(frozen=True)
class AdapterRequest:
    """One authoritative adapter ingress: a turn identifier plus canonical Vera IR."""
    turn_id: str
    ir: "VeraIR"

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
    if not request.turn_id or response.turn_id != request.turn_id:
        raise ValueError("turn identity mismatch")
    if not response.provider or not response.model:
        raise ValueError("missing model provenance")
    return response
