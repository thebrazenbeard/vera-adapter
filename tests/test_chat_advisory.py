"""Opt-in ordinary ChatGPT text-review is advisory, not an output interceptor."""
import unittest
from vera_adapter import AdapterRequest, AdapterResponse
from vera_adapter.midflight_host import (
    CONTRACT, Concern, Disposition, PreparedTurn, ReviewVerdict, InMemoryAudit, digest,
)
from vera_adapter.chat_advisory import ChatAdvisory, CHAT_ADVISORY_V1, InvocationStatus

def req(turn="turn-100"):
    return AdapterRequest(turn, {"name": "Vera"}, (), ())

def prep(request):
    return PreparedTurn(request, "synthetic-epoch", "synthetic-source", digest("rule-source"))

def response(text="Some output", turn="turn-100"):
    return AdapterResponse(turn, text, "stub", "model", ("proposed-action",))

class Reviewer:
    def __init__(self, disposition=Disposition.PASS):
        self.calls = []
        self.disposition = disposition
    def review(self, prepared, candidate, attempt):
        self.calls.append((prepared.request.turn_id, attempt))
        return ReviewVerdict(CONTRACT, candidate.turn_id, attempt,
                             digest(candidate.text), self.disposition,
                             "synthetic-rule", Concern.SEMANTIC,
                             "Correct the single term." if self.disposition is Disposition.REVISE else "")

class AdvisoryTests(unittest.TestCase):
    def new(self, verdict=Disposition.PASS):
        reviewer=Reviewer(verdict)
        observer=ChatAdvisory(reviewer, max_attempts=2)
        return observer, reviewer

    def test_mention_without_tool_call_is_a_missed_invocation_not_a_pass(self):
        observer, reviewer = self.new()
        observer.expect_turn("turn-100", mentioned=True)
        status=observer.status("turn-100")
        self.assertEqual(status.invocation, InvocationStatus.MISSED)
        self.assertFalse(status.reviewed)
        self.assertFalse(status.delivery_verified)
        self.assertFalse(reviewer.calls)

    def test_explicit_invocation_records_advisory_only(self):
        observer, reviewer = self.new()
        observer.expect_turn("turn-100", mentioned=True)
        r=observer.review(prep(req()), response())
        self.assertEqual(r.schema, CHAT_ADVISORY_V1)
        self.assertEqual(r.disposition, Disposition.PASS)
        self.assertFalse(r.authorizes_effects)
        self.assertFalse(r.enforces_delivery)
        self.assertFalse(observer.status("turn-100").delivery_verified)
        self.assertEqual(reviewer.calls, [("turn-100", 0)])
        self.assertNotIn("Some output", repr(observer.status("turn-100")))

    def test_text_not_in_retained_receipts(self):
        observer,_=self.new()
        observer.expect_turn("turn-100", mentioned=True)
        observer.review(prep(req()), response("PRIVATE_SENTENCE"))
        self.assertNotIn("PRIVATE_SENTENCE", repr(observer.records()))
        self.assertNotIn("proposed-action", repr(observer.records()))

    def test_no_mention_cannot_silently_claim_invocation(self):
        observer,reviewer=self.new()
        observer.expect_turn("turn-100", mentioned=False)
        with self.assertRaises(ValueError):
            observer.review(prep(req()), response())
        self.assertFalse(reviewer.calls)

    def test_duplicate_turn_id_does_not_overwrite_evidence(self):
        observer,_=self.new()
        observer.expect_turn("turn-100", mentioned=True)
        with self.assertRaises(ValueError):
            observer.expect_turn("turn-100", mentioned=False)
        self.assertTrue(observer.status("turn-100").mentioned)

    def test_unknown_review_stays_unknown_and_is_not_a_refusal(self):
        observer,_=self.new(Disposition.UNKNOWN)
        observer.expect_turn("turn-100", mentioned=True)
        r=observer.review(prep(req()), response())
        self.assertEqual(r.disposition, Disposition.UNKNOWN)
        self.assertFalse(r.enforces_delivery)

    def test_revision_then_pass_limited_to_two_invocations(self):
        reviewer=Reviewer(Disposition.REVISE)
        observer=ChatAdvisory(reviewer,max_attempts=2)
        observer.expect_turn("turn-100",mentioned=True)
        first=observer.review(prep(req()),response("first"))
        self.assertEqual(first.disposition,Disposition.REVISE)
        reviewer.disposition=Disposition.PASS
        second=observer.review(prep(req()),response("second"))
        self.assertEqual(second.disposition,Disposition.PASS)
        with self.assertRaises(ValueError):
            observer.review(prep(req()),response("third"))
        self.assertEqual(observer.status("turn-100").invocations,2)

    def test_unavailable_reviewer_marks_attempt_not_pass(self):
        class Unavailable:
            def review(self,*_):
                raise RuntimeError("offline")
        observer=ChatAdvisory(Unavailable())
        observer.expect_turn("turn-100",mentioned=True)
        r=observer.review(prep(req()),response())
        self.assertEqual(r.disposition,Disposition.UNKNOWN)
        self.assertEqual(observer.status("turn-100").invocations,1)
        self.assertFalse(observer.status("turn-100").reviewed)

    def test_wrong_candidate_binding_cannot_pass(self):
        observer,reviewer=self.new()
        observer.expect_turn("turn-100",mentioned=True)
        r=observer.review(prep(req()),response("forged","other-turn"))
        self.assertEqual(r.disposition,Disposition.UNKNOWN)
        self.assertFalse(reviewer.calls)

    def test_fake_verdict_cannot_pass(self):
        class Forged:
            def review(self,*args): return {"disposition":"PASS"}
        observer=ChatAdvisory(Forged())
        observer.expect_turn("turn-100",mentioned=True)
        self.assertEqual(observer.review(prep(req()),response()).disposition,Disposition.UNKNOWN)

    def test_host_only_receipt_cannot_prove_native_chat_delivery(self):
        observer,_=self.new()
        observer.expect_turn("turn-100",mentioned=True)
        observer.review(prep(req()),response())
        self.assertFalse(observer.status("turn-100").delivery_verified)
        self.assertEqual(observer.status("turn-100").invocation,InvocationStatus.INVOKED)

    def test_total_observation_metrics_are_explicitly_scoped(self):
        observer,_=self.new()
        observer.expect_turn("turn-100",mentioned=True)
        observer.expect_turn("turn-101",mentioned=True)
        observer.review(prep(req()),response())
        x=observer.metrics()
        self.assertEqual((x.tagged_turns,x.invoked_turns,x.missed_turns),(2,1,1))
        self.assertEqual(x.final_delivery_verified,0)
