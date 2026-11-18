"""Opt-in ChatGPT text-turn review experiment: advisory only, no interception.

The host (or test fixture) must separately observe user intent and each actual
tool invocation. A model claiming it called a plugin is not such an observation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
import re

from .core import AdapterResponse
from .midflight_host import (
    Disposition, HostGate, PreparedTurn, ReviewVerdict, digest,
)

CHAT_ADVISORY_V1 = "VERA_CHAT_ADVISORY_V1"
_TURN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


class InvocationStatus(str, Enum):
    UNTAGGED = "UNTAGGED"
    MISSED = "MISSED"
    INVOKED = "INVOKED"


@dataclass(frozen=True, slots=True)
class ChatReviewReceipt:
    schema: str
    turn_fingerprint: str
    attempt: int
    candidate_digest: str
    disposition: Disposition
    revision_hint: str
    authorizes_effects: bool = False
    enforces_delivery: bool = False


@dataclass(frozen=True, slots=True)
class ChatReviewStatus:
    turn_fingerprint: str
    mentioned: bool
    invocation: InvocationStatus
    invocations: int
    reviewed: bool
    last_disposition: Disposition | None
    delivery_verified: bool = False


@dataclass(frozen=True, slots=True)
class ChatReviewMetrics:
    tagged_turns: int
    invoked_turns: int
    missed_turns: int
    reviewed_turns: int
    final_delivery_verified: int = 0


class ChatAdvisory:
    """Ephemeral opt-in ledger for synthetic, observable per-turn invocation.

    This is not an MCP server, not a ChatGPT turn hook, not durable transport,
    and not a real observer of the final assistant message. It can only attest
    that THIS Python object was called on registered host-claimed inputs.
    """
    def __init__(self, reviewer, *, max_attempts: int = 2):
        if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
            raise ValueError("max_attempts must be an integer in 1..3")
        self._reviewer = reviewer
        self._max_attempts = max_attempts
        self._turns: dict[str, dict] = {}
        self._lock = RLock()

    def expect_turn(self, turn_id: str, *, mentioned: bool) -> None:
        if type(turn_id) is not str or _TURN.fullmatch(turn_id) is None:
            raise ValueError("invalid turn identifier")
        if type(mentioned) is not bool:
            raise ValueError("mentioned must be a host-claimed boolean")
        with self._lock:
            if turn_id in self._turns:
                raise ValueError("duplicate or conflicting turn intent")
            self._turns[turn_id] = {
                "mentioned": mentioned,
                "invocations": 0,
                "reviewed": False,
                "last": None,
                "candidate_digest": "",
            }

    def review(self, prepared: PreparedTurn, candidate: AdapterResponse) -> ChatReviewReceipt:
        if (type(prepared) is not PreparedTurn or
                type(prepared.request.turn_id) is not str):
            raise ValueError("invalid host preflight request")
        turn_id = prepared.request.turn_id
        with self._lock:
            state = self._turns.get(turn_id)
            if state is None or not state["mentioned"]:
                raise ValueError("no registered opted-in turn")
            if state["invocations"] >= self._max_attempts:
                raise ValueError("advisory attempt limit")
            if state["invocations"] and state["last"] is not Disposition.REVISE:
                raise ValueError("only explicit revision can trigger another review")
            attempt = state["invocations"]
            state["invocations"] += 1  # actual call observed, even if failed
            result = Disposition.UNKNOWN
            candidate_digest = ""
            hint = ""
            try:
                if type(candidate) is not AdapterResponse or candidate.turn_id != turn_id:
                    raise ValueError("candidate turn mismatch")
                candidate = HostGate._candidate(prepared.request, candidate)
                candidate_digest = digest(candidate.text)
                decision = self._reviewer.review(prepared, candidate, attempt)
                if not HostGate._valid_review(decision, candidate, attempt):
                    raise ValueError("invalid review reply")
                result = decision.disposition
                hint = decision.revision_hint if result is Disposition.REVISE else ""
                state["reviewed"] = True
            except Exception:
                result = Disposition.UNKNOWN
            state["candidate_digest"] = candidate_digest
            state["last"] = result
            return ChatReviewReceipt(
                CHAT_ADVISORY_V1, digest(turn_id), attempt, candidate_digest,
                result, hint,
            )

    def status(self, turn_id: str) -> ChatReviewStatus:
        with self._lock:
            record = self._turns[turn_id]
            invocation = (
                InvocationStatus.INVOKED if record["invocations"] else
                InvocationStatus.MISSED if record["mentioned"] else
                InvocationStatus.UNTAGGED
            )
            return ChatReviewStatus(
                digest(turn_id), record["mentioned"], invocation,
                record["invocations"], record["reviewed"], record["last"],
            )

    def records(self) -> tuple[ChatReviewStatus, ...]:
        with self._lock:
            return tuple(self.status(turn) for turn in sorted(self._turns))

    def metrics(self) -> ChatReviewMetrics:
        with self._lock:
            records = self.records()
            tagged = sum(x.mentioned for x in records)
            invoked = sum(x.invocation is InvocationStatus.INVOKED for x in records)
            reviewed = sum(x.reviewed for x in records)
            return ChatReviewMetrics(tagged, invoked, tagged-invoked, reviewed)
