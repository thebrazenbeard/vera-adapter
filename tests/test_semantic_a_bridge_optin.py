"""B tests against exact unmerged A source, opt-in via A_SOURCE env var.

No provider/model call or real user authentication. Do not count a skipped
test as verified A integration. Source pin must match before assertion.
"""
from dataclasses import replace
from hashlib import sha1
from pathlib import Path
import os
import subprocess
import unittest

from tests.test_semantic_bridge_compat import multi_rule_subject
from tests.test_semantic_correction import VERIFIER
from vera_adapter.semantic_bridge_compat import review_for_engineer_a_v1
from vera_adapter.semantic_correction import review_candidate


A_HEAD="a6b0405cd1ee9f83ea8c25798a9b9cd605518c8b"
A_BRIDGE_BLOB="695d83e98016ba9a2da7f5051c13bf4a41427a24"
A_SOURCE=os.environ.get("VERA_ADAPTER_A_BRIDGE_SOURCE_ROOT","")


@unittest.skipUnless(A_SOURCE,"explicit A source root not provided")
class ExactASourceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root=Path(A_SOURCE).resolve()
        actual=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
        assert actual==A_HEAD, (actual,A_HEAD)
        content=(root/"vera_adapter"/"midflight_b_bridge.py").read_bytes()
        digest=sha1(b"blob "+str(len(content)).encode("ascii")+b"\0"+content).hexdigest()
        assert digest==A_BRIDGE_BLOB,(digest,A_BRIDGE_BLOB)
        import vera_adapter
        vera_adapter.__path__.append(str(root/"vera_adapter"))
        from vera_adapter.midflight_b_bridge import EngineerBReviewPort
        from vera_adapter.midflight_host import PreparedTurn,digest as hash_text
        from vera_adapter.core import AdapterRequest,AdapterResponse
        cls.port=EngineerBReviewPort
        cls.prepared=PreparedTurn
        cls.hash_text=staticmethod(hash_text)
        cls.req=AdapterRequest
        cls.response=AdapterResponse

    def _case(self):
        q=multi_rule_subject()
        req=self.req("turn-001",{"role":"synthetic"},(),("Correct two things",))
        cand=self.response("turn-001",q.response.text,"fixture","fixture-model")
        prep=self.prepared(req,"source-rule","source-only",self.hash_text("rule"))
        return q,prep,cand

    def test_multihint_raw_unknown_bounded_revise(self):
        q,prep,cand=self._case()
        builder=lambda p,c,a: replace(q,request=p.request,response=c)
        raw=self.port(builder,lambda s:review_candidate(s,VERIFIER))
        bounded=self.port(builder,lambda s:review_for_engineer_a_v1(s,VERIFIER))
        before=raw.review(prep,cand,0)
        after=bounded.review(prep,cand,0)
        self.assertEqual(before.disposition.value,"UNKNOWN")
        self.assertEqual(after.disposition.value,"REVISE")
        self.assertEqual(after.candidate_digest,self.hash_text(cand.text))
        self.assertLessEqual(len(after.revision_hint.encode("utf-8")),256)
        self.assertIn("apology",after.revision_hint)
        self.assertIn("playful request",after.revision_hint)

    def test_unauthenticated_cached_pass_callback_is_not_detected_negative(self):
        # KNOWN UNQUALIFIED HOST TRUST LIMITATION. A structurally valid old
        # PASS can be returned by a dishonest or miswired callback. A cannot
        # authenticate an independent semantic assessment from V1 schema.
        q,prep,cand=self._case()
        good=replace(q,response=replace(q.response,text="Ha, okay."))
        cached=review_candidate(good,VERIFIER)
        self.assertEqual(cached.decision,"PASS")
        port=self.port(lambda p,c,a:replace(q,request=p.request,response=c),
                       lambda ignored:cached)
        result=port.review(prep,cand,0)
        self.assertEqual(result.disposition.value,"PASS")
        self.assertEqual(result.reason_code,"B_PASS")
        # This is a falsifier of real callback honesty, not a success claim.


if __name__=="__main__":
    unittest.main()