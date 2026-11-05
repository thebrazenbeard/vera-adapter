"""Model-neutral Vera invocation contracts. No tool effects are executed here."""
from dataclasses import dataclass
from typing import Protocol, Mapping


class _FrozenIdentity(dict):
    """JSON/asdict-compatible identity snapshot; mutators fail closed."""

    def _readonly(self, *args, **kwargs):
        raise TypeError("identity is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _readonly

    def __ior__(self, other):
        return self._readonly(other)


@dataclass(frozen=True)
class AdapterRequest:
    turn_id: str
    identity: Mapping[str, str]
    continuity: tuple[str, ...]
    conversation: tuple[str, ...]
    capabilities: tuple[str, ...] = ()
    authority: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Detach the identity from caller-owned mutable state before routing."""
        if not isinstance(self.identity, Mapping):
            raise TypeError("identity must be a mapping")
        snapshot = dict(self.identity)
        if any(type(key) is not str or type(value) is not str
               for key, value in snapshot.items()):
            raise ValueError("identity requires string keys and values")
        object.__setattr__(self, "identity", _FrozenIdentity(snapshot))
        # A frozen dataclass does not freeze nested caller-owned lists. These
        # model/authority vectors must be canonical immutable string tuples.
        for field in ("continuity", "conversation", "capabilities", "authority"):
            values = getattr(self, field)
            if type(values) is not tuple or any(type(value) is not str for value in values):
                raise TypeError(f"AdapterRequest.{field} requires string tuple")

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
