"""Engineer B: strict synthetic compatibility with A single-hint V1 bridge."""
from dataclasses import replace
import unittest

from tests.test_semantic_correction import VERIFIER, request, rule, signed
from vera_adapter.semantic_correction import review_candidate, ReviewDecision
from vera_adapter.semantic_bridge_compat import (
    review_for_engineer_a_v1, normalize_for_engineer_a_v1,
)


def multi_rule_subject(*, reverse=False):
    first = rule(
        rule_id="avoid_detour", kind="PREFERENCE", check="META_DETOUR",
        scope_tags=("playful",), scope_referent="dialogue", forbidden="as an ai",
    )
    second = rule(
        rule_id="apology_loop", kind="PREFERENCE", check="APOLOGY_LOOP",
        scope_tags=("apology",), scope_referent="dialogue", forbidden="i'm sorry",
    )
    records = [signed(first), signed(second)]
    if reverse:
        records.reverse()
    return request(
        "As an AI, I'm sorry. I promise I'll do better.",
        corrections=records, tags=("playful", "apology"), referent="dialogue",
        user="Please tell a joke and fix the inventory clue.",
        previous=("I'm sorry. I promise I'll do better.",),
    )


class SemanticBridgeCompatTests(unittest.TestCase):
    def test_reproduced_v1_multi_hint_mismatch_is_consolidated(self):
        q=multi_rule_subject()
        original=review_candidate(q,VERIFIER)
        self.assertEqual(original.decision,"REVISE")
        self.assertEqual(len(original.revision_guidance),2)
        adjusted=review_for_engineer_a_v1(q,VERIFIER)
        self.assertEqual(adjusted.decision,"REVISE")
        self.assertEqual(len(adjusted.revision_guidance),1)
        self.assertLessEqual(len(adjusted.revision_guidance[0].encode("utf-8")),256)
        for item in original.revision_guidance:
            self.assertIn(item,adjusted.revision_guidance[0])
        self.assertEqual(adjusted.reason_codes,original.reason_codes)
        self.assertEqual(adjusted.applicable_rule_ids,original.applicable_rule_ids)
        self.assertFalse(adjusted.authorizes_effects)
        self.assertFalse(adjusted.updates_memory)
        self.assertFalse(adjusted.proves_subjective_state)

    def test_different_input_order_yields_same_bounded_hint(self):
        q1=multi_rule_subject()
        q2=multi_rule_subject(reverse=True)
        self.assertEqual(
            review_for_engineer_a_v1(q1,VERIFIER).revision_guidance,
            review_for_engineer_a_v1(q2,VERIFIER).revision_guidance
        )

    def test_single_rule_good_answer_keeps_exact_pass(self):
        q=request("Ha, the fictional kettle is a comedian!")
        original=review_candidate(q,VERIFIER)
        adjusted=normalize_for_engineer_a_v1(original)
        self.assertIs(adjusted,original)
        self.assertEqual(adjusted.decision,"PASS")

    def test_unbounded_multi_hint_fails_unknown_without_silent_drop(self):
        good=review_candidate(multi_rule_subject(),VERIFIER)
        test=replace(good,revision_guidance=("A"*210,"B"*210))
        bounded=normalize_for_engineer_a_v1(test)
        self.assertEqual(bounded.decision,"UNKNOWN")
        self.assertIn("BRIDGE_GUIDANCE_TOO_LARGE",bounded.reason_codes)
        self.assertEqual(bounded.revision_guidance,())
        self.assertFalse(bounded.authorizes_effects)

    def test_degenerate_or_malformed_hint_yields_unknown(self):
        orig=review_candidate(multi_rule_subject(),VERIFIER)
        for texts in (("   ","meaningful"),("valid",3),tuple("X" for _ in range(9))):
            with self.subTest(hints=texts):
                out=normalize_for_engineer_a_v1(replace(orig,revision_guidance=texts))
                self.assertEqual(out.decision,"UNKNOWN")
                self.assertEqual(out.revision_guidance,())


if __name__=="__main__":
    unittest.main()