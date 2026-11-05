"""Provider-neutral adapter seam."""
from dataclasses import dataclass
from typing import Callable, Protocol
from .core import AdapterRequest, AdapterResponse, validate_response
from .continuity import ContinuityFact
from .ir import VeraIR

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

def render_envelope(
    request: AdapterRequest,
    *,
    verify_ir: Callable[[VeraIR], bool] | None = None,
    admitted_correction: Callable[[ContinuityFact], bool] | None = None,
) -> ProviderEnvelope:
    """Project only host-verified complete IR into provider system context.

    The host owns this callback; untrusted source references and self-declared
    backing flags are attributes, not proof. Missing/failed verification denies.
    """
    ir = request.ir
    if verify_ir is None:
        raise PermissionError("provider context requires host-verified VeraIR")
    try:
        verified = verify_ir(ir)
    except Exception as exc:
        raise PermissionError("VeraIR source verification failed") from exc
    if verified is not True:
        raise PermissionError("VeraIR source verification denied")
    return ProviderEnvelope(
        request.turn_id,
        ir.context(admitted_correction=admitted_correction),
        ir.conversation,
        ir.capabilities,
    )

class UniversalAdapter:
    def __init__(
        self,
        driver: ProviderDriver,
        *,
        verify_ir: Callable[[VeraIR], bool] | None = None,
        admitted_correction: Callable[[ContinuityFact], bool] | None = None,
    ):
        self.driver = driver
        self.verify_ir = verify_ir
        self.admitted_correction = admitted_correction

    def invoke(self, request: AdapterRequest) -> AdapterResponse:
        envelope = render_envelope(
            request,
            verify_ir=self.verify_ir,
            admitted_correction=self.admitted_correction,
        )
        text = self.driver.complete(envelope)
        return validate_response(request, AdapterResponse(request.turn_id, text, self.driver.provider, self.driver.model))
