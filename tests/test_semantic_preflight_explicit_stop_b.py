"""Narrow safety negative: plainly explicit stop contradicts caller act labels.

No broad sentiment/consent classifier. Even this check is not real host
identity or provider input qualification. QUOTE/HYPOTHETICAL bypass.
"""
from __future__ import annotations
from tests.test_semantic_preflight import ISSUER, rec, request
from vera_adapter.semantic_preflight import plan_preflight
import unittest

class NarrowCurrentTurnStopB(unittest.TestCase):
    def test_plain_stop_contradicts_forged_invitation_before_source_selection(self):
        d=plan_preflight(request(records=(rec(),),act="INVITATION",
            message="Stop this topic."),ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())
        self.assertIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)
        self.assertNotIn("OPTIONAL_NOT_COMPULSORY",d.context_codes)
        self.assertFalse(d.authorizes_effects)

    def test_pressure_label_cannot_override_present_please_stop(self):
        d=plan_preflight(request(records=(rec(),),act="PRESSURE",
            message="Please stop."),ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_task_label_cannot_override_stop_now(self):
        d=plan_preflight(request(act="TASK",message="Stop now!"),ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_honest_topic_shift_keeps_current_context(self):
        d=plan_preflight(request(act="TOPIC_SHIFT",message="Stop this topic."),ISSUER)
        self.assertIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)
        self.assertNotIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_quoted_stop_is_not_a_live_stop(self):
        d=plan_preflight(request(act="QUOTE",message='"Stop this topic."'),ISSUER)
        self.assertIn("MENTION_NOT_LIVE_INVITATION",d.context_codes)
        self.assertNotIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_dont_stop_is_not_a_refusal(self):
        d=plan_preflight(request(act="INVITATION",message="Please don't stop."),ISSUER)
        self.assertEqual(d.decision,"REVISE")
        self.assertNotIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_stop_in_mid_sentence_not_a_direct_command(self):
        d=plan_preflight(request(act="INVITATION",message="I can't stop thinking about this."),ISSUER)
        self.assertEqual(d.decision,"REVISE")
        self.assertNotIn("CURRENT_TURN_ACT_CONFLICT",d.reason_codes)

    def test_no_current_source_text_interpolated_into_unknown(self):
        private="Stop this conversation."
        d=plan_preflight(request(records=(rec(),),act="INVITATION",message=private),ISSUER)
        self.assertFalse(d.selected_sources)
        self.assertNotIn(private," ".join(d.recommended_context))
        self.assertFalse(d.updates_memory)

if __name__ == "__main__":
    unittest.main()