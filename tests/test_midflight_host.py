"""Source-only synthetic tests for Engineer A's host delivery gate."""
import hashlib
import json
import unittest

from vera_adapter import AdapterRequest, AdapterResponse
from vera_adapter.midflight_host import (
    CONTRACT, Concern, Disposition, ReviewVerdict, PreparedTurn, BufferedStream,
    DeliveryAck, Outcome, HostGate, InMemoryReplay, InMemoryDelivery, InMemoryAudit,
)

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def request(turn="turn-001"):
    return AdapterRequest(turn, {"name": "Vera"}, (), ())

class Authority:
    def __init__(self):
        self.fail_at = None
        self.checks = []
        self.raise_at = None
    def prepare(self, req):
        return PreparedTurn(req, "NO_ACTIVE_CORRECTION_HOST_CHECKED",
                            "synthetic-host", digest("current-source"))
    def current(self, prepared, phase):
        self.checks.append(phase)
        if phase == self.raise_at:
            raise RuntimeError("offline")
        return phase != self.fail_at

class Producer:
    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []
    def generate(self, req, attempt, hint):
        self.calls.append((req.turn_id, attempt, hint))
        result = self.outputs[attempt]
        if isinstance(result, Exception):
            raise result
        return result

class Reviewer:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.bad_digest = False
        self.bad_turn = False
    def review(self, prepared, candidate, attempt):
        self.calls.append((attempt, candidate.text))
        decision = self.outcomes[attempt]
        if isinstance(decision, Exception):
            raise decision
        if not isinstance(decision, Disposition):
            return decision
        return ReviewVerdict(
            CONTRACT, "different" if self.bad_turn else candidate.turn_id,
            attempt, "f"*64 if self.bad_digest else digest(candidate.text),
            decision, "synthetic-review", Concern.HARD if decision == Disposition.BLOCK
            else Concern.SEMANTIC, "revise wording" if decision == Disposition.REVISE else "",
        )

def candidate(text="Approved text.", *, turn="turn-001", actions=()):
    return AdapterResponse(turn, text, "synthetic", "model", actions)

class GateTests(unittest.TestCase):
    def setup_gate(self, outputs, decisions, *, max_revisions=1, authority=None,
                   delivery=None, replay=None, audit=None):
        self.authority = authority or Authority()
        self.producer = Producer(*outputs)
        self.reviewer = Reviewer(*decisions)
        self.delivery = delivery or InMemoryDelivery()
        self.audit = audit or InMemoryAudit()
        self.replay = replay or InMemoryReplay()
        self.gate = HostGate(self.authority, self.producer, self.reviewer,
                             self.delivery, self.replay, self.audit,
                             max_revisions=max_revisions)
        return self.gate

    def test_pass_candidate_delivered_byte_identical(self):
        self.setup_gate([candidate()], [Disposition.PASS])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.DELIVERED)
        self.assertEqual(self.delivery.records, [("turn-001", "Approved text.", digest("Approved text."))])
        self.assertEqual(self.producer.calls, [("turn-001", 0, "")])
        self.assertEqual(self.authority.checks, ["dispatch", "delivery"])

    def test_forbidden_candidate_never_published(self):
        self.setup_gate([candidate("FORBIDDEN_BLOB")], [Disposition.BLOCK])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.BLOCKED)
        self.assertEqual(self.delivery.records, [])
        self.assertFalse(any("FORBIDDEN_BLOB" in repr(record) for record in self.audit.records))

    def test_revision_is_bounded_and_only_second_pass_delivers(self):
        self.setup_gate([candidate("bad secret"), candidate("Corrected.")],
                        [Disposition.REVISE, Disposition.PASS])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.DELIVERED)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(self.delivery.records[0][1], "Corrected.")
        self.assertEqual(len(self.producer.calls), 2)

    def test_revision_exhaustion_withholds_not_fake_refusal(self):
        self.setup_gate([candidate("a"), candidate("b")],
                        [Disposition.REVISE, Disposition.REVISE])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.WITHHELD)
        self.assertEqual(result.reason, "REVISION_LIMIT")
        self.assertFalse(self.delivery.records)

    def test_unavailable_verifier_never_silently_passes(self):
        self.setup_gate([candidate()], [RuntimeError("verifier offline")])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.delivery.records)

    def test_malformed_verifier_never_silently_passes(self):
        self.setup_gate([candidate()], [{"disposition": "PASS"}])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.delivery.records)

    def test_unknown_style_does_not_become_a_refusal_message(self):
        self.setup_gate([candidate()], [Disposition.UNKNOWN])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.WITHHELD)
        self.assertNotEqual(result.outcome, Outcome.BLOCKED)
        self.assertFalse(self.delivery.records)

    def test_stale_correction_prevents_candidate_generation(self):
        a = Authority(); a.fail_at = "dispatch"
        self.setup_gate([candidate()], [Disposition.PASS], authority=a)
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.BLOCKED)
        self.assertEqual(self.producer.calls, [])
        self.assertFalse(self.delivery.records)

    def test_revoked_before_delivery_prevents_text_escape(self):
        a = Authority(); a.fail_at = "delivery"
        self.setup_gate([candidate("EXFIL")], [Disposition.PASS], authority=a)
        self.assertEqual(self.gate.run(request()).outcome, Outcome.BLOCKED)
        self.assertEqual(self.delivery.records, [])

    def test_unavailable_authority_prevents_dispatch(self):
        a = Authority(); a.raise_at = "dispatch"
        self.setup_gate([candidate()], [Disposition.PASS], authority=a)
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertEqual(self.producer.calls, [])

    def test_duplicate_turn_id_is_deterministically_rejected(self):
        self.setup_gate([candidate()], [Disposition.PASS])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.DELIVERED)
        again = self.gate.run(request())
        self.assertEqual(again.outcome, Outcome.BLOCKED)
        self.assertEqual(again.reason, "DUPLICATE_TURN")
        self.assertEqual(len(self.delivery.records), 1)
        self.assertEqual(len(self.producer.calls), 1)

    def test_conflicting_review_digest_fails_closed(self):
        self.setup_gate([candidate()], [Disposition.PASS])
        self.reviewer.bad_digest = True
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.delivery.records)

    def test_conflicting_review_turn_fails_closed(self):
        self.setup_gate([candidate()], [Disposition.PASS])
        self.reviewer.bad_turn = True
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)

    def test_stream_is_withheld_until_complete_and_reviewed(self):
        def fragments():
            yield "UNVERIFIED_"
            self.assertEqual(self.delivery.records, [])
            yield "TEXT"
        stream = BufferedStream("turn-001", "synthetic", "model", fragments())
        self.setup_gate([stream], [Disposition.BLOCK])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.BLOCKED)
        self.assertFalse(self.delivery.records)

    def test_stream_interruption_never_leaks_chunks(self):
        def fragments():
            yield "PRIVATE_CHUNK"
            raise IOError("stream interrupted")
        self.setup_gate([BufferedStream("turn-001", "synthetic", "model", fragments())],
                        [Disposition.PASS])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.delivery.records)

    def test_proposed_actions_never_execute_as_result_of_pass(self):
        executed = []
        self.setup_gate([candidate("Safe.", actions=("delete-database",))], [Disposition.PASS])
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.DELIVERED)
        self.assertEqual(executed, [])
        self.assertEqual(self.delivery.records[0][1], "Safe.")
        self.assertTrue(any(a.proposed_action_count == 1 for a in self.audit.records))

    def test_revision_cannot_swap_provider_or_model(self):
        first = candidate("bad")
        second = AdapterResponse("turn-001", "better", "other-provider", "model")
        self.setup_gate([first, second], [Disposition.REVISE, Disposition.PASS])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.delivery.records)

    def test_delivery_ack_mismatch_is_ambiguous_not_retry(self):
        class BadSink(InMemoryDelivery):
            def publish(self, turn_id, text, candidate_digest):
                super().publish(turn_id, text, candidate_digest)
                return DeliveryAck(turn_id, "0"*64, True)
        sink = BadSink()
        self.setup_gate([candidate()], [Disposition.PASS], delivery=sink)
        result = self.gate.run(request())
        self.assertEqual(result.outcome, Outcome.DELIVERY_UNKNOWN)
        self.assertEqual(len(sink.records), 1)
        self.assertEqual(len(self.producer.calls), 1)

    def test_telemetry_contains_no_candidate_or_reviewer_text(self):
        self.setup_gate([candidate("SECRET_1234")], [Disposition.PASS])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.DELIVERED)
        payload = repr(self.audit.records)
        self.assertNotIn("SECRET_1234", payload)
        self.assertNotIn("Approved text.", payload)

    def test_review_reason_code_not_recorded_as_private_text(self):
        class Sensitive(Reviewer):
            def review(self, prepared, candidate, attempt):
                return ReviewVerdict(CONTRACT, candidate.turn_id, attempt,
                                     digest(candidate.text), Disposition.PASS,
                                     "SECRET_PRIVATE_LABEL", Concern.SEMANTIC)
        self.setup_gate([candidate("safe")], [Disposition.PASS])
        self.gate.reviewer = Sensitive(Disposition.PASS)
        self.assertEqual(self.gate.run(request()).outcome, Outcome.DELIVERED)
        self.assertNotIn("SECRET_PRIVATE_LABEL", repr(self.audit.records))

    def test_host_rejects_preflight_authority_rebinding(self):
        class Privileged(Authority):
            def prepare(self, req):
                modified = AdapterRequest(req.turn_id, req.identity, req.continuity,
                                          req.conversation, req.capabilities, ("administrator",))
                return PreparedTurn(modified, "forged", "fake", digest("fake"))
        self.setup_gate([candidate()], [Disposition.PASS], authority=Privileged())
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertEqual(self.producer.calls, [])

    def test_producer_cannot_mutate_caller_identity(self):
        self.setup_gate([candidate()], [Disposition.PASS])
        def mutable(req, attempt, hint):
            req.identity["permission"] = "admin"
            return candidate()
        self.gate.producer.generate = mutable
        supplied = request()
        self.assertEqual(self.gate.run(supplied).outcome, Outcome.WITHHELD)
        self.assertNotIn("permission", supplied.identity)
        self.assertFalse(self.delivery.records)

    def test_prepare_malformed_fails_closed_before_generation(self):
        class Broken(Authority):
            def prepare(self, req):
                return {"looks": "authorized"}
        self.setup_gate([candidate()], [Disposition.PASS], authority=Broken())
        self.assertEqual(self.gate.run(request()).outcome, Outcome.WITHHELD)
        self.assertFalse(self.producer.calls)

    def test_revision_cannot_force_tool_effect_by_hint(self):
        self.setup_gate([candidate("bad", actions=("run-shell",)),
                         candidate("safe", actions=("run-shell",))],
                        [Disposition.REVISE, Disposition.PASS])
        self.assertEqual(self.gate.run(request()).outcome, Outcome.DELIVERED)
        self.assertEqual(self.delivery.records[0][1], "safe")
        self.assertEqual(len(self.producer.calls), 2)


if __name__ == "__main__":
    unittest.main()
