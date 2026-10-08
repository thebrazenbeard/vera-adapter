"""Provider-neutral adapter seam."""
from dataclasses import dataclass
from typing import Protocol
from .core import AdapterRequest, AdapterResponse, validate_response

@dataclass(frozen=True)
class ProviderEnvelope:
    turn_id: str
    system_context: tuple[str, ...]
    conversation: tuple[str, ...]
    capabilities: tuple[str, ...]

class ProviderDriver(Protocol):
    provider: str
    model: str
    def complete(self, envelope: ProviderEnvelope) -> str: ...

def render_envelope(request: AdapterRequest) -> ProviderEnvelope:
    identity = tuple(f"{k}: {v}" for k, v in sorted(request.identity.items()))
    return ProviderEnvelope(request.turn_id, identity + request.continuity, request.conversation, request.capabilities)

class UniversalAdapter:
    def __init__(self, driver: ProviderDriver): self.driver = driver
    def invoke(self, request: AdapterRequest) -> AdapterResponse:
        text = self.driver.complete(render_envelope(request))
        return validate_response(request, AdapterResponse(request.turn_id, text, self.driver.provider, self.driver.model))
