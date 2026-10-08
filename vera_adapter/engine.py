"""Universal cognitive-engine capability contract.

Provider names are provenance only. Vera semantics never branch on them.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class EngineCapabilities:
    context_window: int | None = None
    structured_output: bool = False
    tool_calls: bool = False
    multimodal_input: bool = False
    reasoning_controls: bool = False

@dataclass(frozen=True)
class EngineDescriptor:
    engine_id: str
    provider: str
    model: str
    capabilities: EngineCapabilities = EngineCapabilities()

def capability_fingerprint(engine: EngineDescriptor) -> tuple[object, ...]:
    c = engine.capabilities
    return (c.context_window, c.structured_output, c.tool_calls, c.multimodal_input, c.reasoning_controls)
