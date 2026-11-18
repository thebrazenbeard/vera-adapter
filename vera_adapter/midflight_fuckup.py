"""Optional F.U.C.K.U.P. session-preflight bridge for the midflight host gate.

No source states are promoted here. This module reads the exact F.U.C.K.U.P.
session-preflight APIs when they are installed by an approved host.
"""
from __future__ import annotations
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from .core import AdapterRequest
from .midflight_host import PreparedTurn


class FuckupPreflightPort:
    """Bind existing verified preflight/currentness to an immutable host turn.

    The assembler must return the EXACT request object, plus the actual trusted
    model-request messages for F.U.C.K.U.P.'s materialization verification.
    A production provider adapter must independently prove these are the real
    outgoing messages; synthetic tests cannot establish provider consumption.
    """
    def __init__(self, *, store, injector, context: Mapping[str, str],
                 expected_target: str, operation_id: str, session_id: str,
                 assemble: Callable):
        self.store = store
        self.injector = injector
        self.context = dict(context)
        self.expected_target = expected_target
        self.operation_id = operation_id
        self.session_id = session_id
        self.assemble = assemble
        self._active = {}

    def prepare(self, request: AdapterRequest) -> PreparedTurn:
        from fuckup_protocol.session_preflight import (
            load_reference_session_preflight, verify_materialized_prompt,
        )
        if request.turn_id in self._active:
            raise RuntimeError("preflight replay within one host")
        preflight = load_reference_session_preflight(
            store=self.store, adapter=self.injector, context=self.context,
            expected_target=self.expected_target, operation_id=self.operation_id,
            session_id=self.session_id,
        )
        material = self.assemble(request, preflight)
        if type(material) is not tuple or len(material) != 2 or material[0] is not request:
            raise RuntimeError("assembler substituted host request")
        proof = verify_materialized_prompt(preflight, material[1])
        if (proof.session_id != preflight.session_id or
                proof.message_digest != preflight.message_digest):
            raise RuntimeError("F.U.C.K.U.P. prompt readback mismatch")
        if (type(preflight.message_digest) is not str
                or not preflight.message_digest.startswith("sha256:")
                or len(preflight.message_digest) != 71):
            raise RuntimeError("unsupported F.U.C.K.U.P. digest")
        if not preflight.source_evidence_ref:
            raise RuntimeError("missing preflight source provenance")
        prepared = PreparedTurn(
            request=request,
            correction_ref=f"{preflight.correction_id}@{preflight.correction_revision}",
            source_ref=preflight.source_evidence_ref,
            source_digest=preflight.message_digest[len("sha256:"):],
        )
        # Only local host cache. Never a durable identity/authentication claim.
        self._active[request.turn_id] = (prepared, preflight)
        return prepared

    def current(self, prepared: PreparedTurn, phase: str) -> bool:
        from fuckup_protocol.session_preflight import verify_dispatch_currentness
        if phase not in ("dispatch", "delivery"):
            raise ValueError("unknown gate currentness phase")
        saved = self._active.get(prepared.request.turn_id)
        if saved is None or saved[0] is not prepared:
            raise RuntimeError("preflight not owned by current host turn")
        verify_dispatch_currentness(
            saved[1], store=self.store, context=self.context,
        )
        return True
