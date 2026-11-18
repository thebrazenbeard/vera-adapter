"""A-owned bridge into Engineer B's versioned semantic review transport."""
from dataclasses import dataclass
import unittest
from vera_adapter import AdapterRequest, AdapterResponse
from vera_adapter.midflight_host import (
    CONTRACT, Concern, Disposition, PreparedTurn, digest,
)
from vera_adapter.midflight_b_bridge import EngineerBReviewPort

@dataclass(frozen=True)
class SemanticRequest:
    schema: str
    request: AdapterRequest
    response: AdapterResponse

@dataclass(frozen=True)
class SemanticDecision:
    schema: str = "VERA_SEMANTIC_REVIEW_DECISION_V1"
    decision: str = "PASS"
    reason_codes: tuple[str,...] = ()
    revision_guidance: tuple[str,...] = ()
    evidence_class: str = "SYNTHETIC_EVALUATION_ONLY"
    authorizes_effects: bool = False
    updates_memory: bool = False
    proves_subjective_state: bool = False

def prepared():
    request=AdapterRequest("t1",{"name":"Vera"},(),())
    return PreparedTurn(request,"source-only","synthetic",digest("rule"))

def candidate(text="okay"):
    return AdapterResponse("t1",text,"synthetic","model",())

class BBridgeTests(unittest.TestCase):
    def make(self, decision=SemanticDecision()):
        seen=[]
        def builder(prep,response,attempt):
            seen.append(("build",attempt))
            return SemanticRequest("VERA_SEMANTIC_REVIEW_REQUEST_V1",prep.request,response)
        def evaluator(subject):
            seen.append(("evaluate",subject.response.text))
            return decision
        return EngineerBReviewPort(builder,evaluator),seen

    def test_accepted_b_pass_stays_advisory_and_bound_to_candidate(self):
        port,seen=self.make()
        x=port.review(prepared(),candidate(),0)
        self.assertEqual(x.disposition,Disposition.PASS)
        self.assertEqual(x.schema,CONTRACT)
        self.assertEqual(x.candidate_digest,digest("okay"))
        self.assertEqual(x.concern,Concern.SEMANTIC)
        self.assertEqual(seen,[("build",0),("evaluate","okay")])

    def test_b_revision_hint_is_bounded(self):
        decision=SemanticDecision(decision="REVISE",revision_guidance=("Use the new term.",))
        port,_=self.make(decision)
        x=port.review(prepared(),candidate(),0)
        self.assertEqual(x.disposition,Disposition.REVISE)
        self.assertEqual(x.revision_hint,"Use the new term.")

    def test_b_block_is_semantic_not_effect_permission(self):
        port,_=self.make(SemanticDecision(decision="BLOCK"))
        review=port.review(prepared(),candidate(),0)
        self.assertEqual(review.disposition,Disposition.BLOCK)
        self.assertEqual(review.concern,Concern.SEMANTIC)

    def test_b_unknown_does_not_turn_into_pass(self):
        port,_=self.make(SemanticDecision(decision="UNKNOWN"))
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)

    def test_forged_effect_authorization_is_quarantined_as_unknown(self):
        port,_=self.make(SemanticDecision(authorizes_effects=True))
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)

    def test_wrong_b_candidate_is_rejected_before_evaluation(self):
        seen=[]
        def builder(prep,response,attempt):
            return SemanticRequest("VERA_SEMANTIC_REVIEW_REQUEST_V1",prep.request,candidate("different"))
        def evaluator(subject):
            seen.append(subject)
            return SemanticDecision()
        port=EngineerBReviewPort(builder,evaluator)
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)
        self.assertFalse(seen)

    def test_bad_decision_schema_fails_closed(self):
        port,_=self.make(SemanticDecision(schema="VERA_WRONG"))
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)

    def test_evaluator_offline_fails_closed(self):
        def builder(prep,response,attempt):
            return SemanticRequest("VERA_SEMANTIC_REVIEW_REQUEST_V1",prep.request,response)
        def offline(req):
            raise RuntimeError("offline")
        port=EngineerBReviewPort(builder,offline)
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)

    def test_private_reason_code_not_copied_to_a_audit(self):
        port,_=self.make(SemanticDecision(reason_codes=("PRIVATE_RULE_TEXT",)))
        x=port.review(prepared(),candidate(),0)
        self.assertNotIn("PRIVATE_RULE_TEXT",repr(x))

    def test_huge_revision_text_not_trimmed_into_false_guidance(self):
        port,_=self.make(SemanticDecision(decision="REVISE",revision_guidance=("X"*400,)))
        self.assertEqual(port.review(prepared(),candidate(),0).disposition,Disposition.UNKNOWN)
