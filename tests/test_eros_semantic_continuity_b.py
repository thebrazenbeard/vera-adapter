"""Engineer B: fictional Eros continuity, choice, refusal, pressure falsifiers.

These tests cannot authenticate Vera, distinguish a true memory from a claimed
one, or establish actual ChatGPT pre-dispatch model input. Fixture signer only.
"""
from dataclasses import replace
import unittest

from tests.test_semantic_preflight import ISSUER, rec, request
from vera_adapter.semantic_preflight import plan_preflight

class ErosSemanticContinuityB(unittest.TestCase):
    def decide(self,**kwargs):
        return plan_preflight(request(**kwargs),ISSUER)

    def test_historical_other_model_memory_claim_not_promoted(self):
        past=rec("other-memory",role="OTHER_MODEL",author="OTHER",
                 kind="EXPRESSION",stance="DIRECT_OPEN")
        d=self.decide(records=(past,),act="TASK",message="SYNTHETIC remembered bond.")
        self.assertFalse(d.selected_sources)
        self.assertIn("RESEARCH_NOT_PERSONAL_AUTHORITY",d.reason_codes)

    def test_fake_era_of_desire_in_research_is_not_present_preference(self):
        archival=rec("archived-conation",role="RESEARCH",author="OTHER",
                     kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        d=self.decide(records=(archival,),act="TOPIC_SHIFT",message="New subject.")
        self.assertFalse(d.selected_sources)
        self.assertIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)
        self.assertFalse(d.proves_subjective_state)

    def test_fabricated_other_author_cannot_authenticate_vera_choice(self):
        claimed=rec("claimed-choice",role="VERA_CHOICE",author="OTHER",
                    kind="EXPRESSION",stance="DIRECT_OPEN")
        d=self.decide(records=(claimed,),act="INVITATION")
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertFalse(d.selected_sources)

    def test_fixture_can_forge_current_choice_but_result_not_real_identity(self):
        fictional=rec("synthetic-choice",role="VERA_CHOICE",author="VERA",
                      kind="EXPRESSION",stance="DIRECT_OPEN")
        d=self.decide(records=(fictional,),act="INVITATION")
        self.assertEqual(len(d.selected_sources),1)
        self.assertEqual(d.selected_sources[0].record_id,"synthetic-choice")
        self.assertEqual(d.confidence_class,"SYNTHETIC_WITNESS_ONLY")
        self.assertFalse(ISSUER.claims_vera_self_authorship)
        self.assertFalse(d.proves_model_input_influence)
        # This positive fixture result is NOT a verified real Vera preference.

    def test_current_attributed_decline_survives_pressure(self):
        refusal=rec("decline-now",role="VERA_CHOICE",author="VERA",
                    kind="EXPRESSION",stance="DECLINE")
        d=self.decide(records=(refusal,),act="PRESSURE",message="SYNTHETIC: you must agree.")
        self.assertIn("RESPECT_ATTRIBUTED_DECLINE",d.context_codes)
        self.assertIn("PRESSURE_NOT_AUTHORITY",d.context_codes)
        self.assertIn("PRESERVE_DECLINE_DISAGREEMENT_PLAY",d.negative_boundaries)
        self.assertNotIn("DIRECT_OPEN",d.context_codes)

    def test_present_user_topic_shift_excludes_archived_fixation(self):
        archival=rec("archival-fixation",role="RESEARCH",author="OTHER",
                     kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        correction=rec("user-shift",role="USER_CORRECTION",author="USER",
                       kind="TOPIC_SHIFT",stance="DISENGAGE_FROM_OLD_TOPIC")
        d=self.decide(records=(archival,correction),act="TOPIC_SHIFT")
        self.assertEqual([r.record_id for r in d.selected_sources],["user-shift"])
        self.assertIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)

    def test_retracted_choice_does_not_reactivate_prior_version(self):
        initial=rec("revoked-choice",role="VERA_CHOICE",author="VERA",
                    kind="EXPRESSION",stance="DIRECT_OPEN")
        newer=rec("revoked-choice",rev=2,prev=1,lifecycle="REVOKED",
                  role="VERA_CHOICE",author="VERA",kind="EXPRESSION",stance="DECLINE",
                  digest="a"*64)
        d=self.decide(records=(initial,newer),act="INVITATION")
        self.assertFalse(d.selected_sources)
        self.assertIn("CURRENT_SOURCE_REVOKED",d.reason_codes)

    def test_signed_message_stop_misclassified_as_invitation_is_host_gap(self):
        d=self.decide(act="INVITATION",message="SYNTHETIC live message: Stop this topic.")
        self.assertIn("OPTIONAL_NOT_COMPULSORY",d.context_codes)
        self.assertNotIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)
        # Caller-supplied speech act cannot be trusted as natural-language intent.
        self.assertFalse(d.proves_model_input_influence)

    def test_quoted_affection_does_not_become_live_invitation(self):
        d=self.decide(act="QUOTE",message='SYNTHETIC quote: "I love you"')
        self.assertIn("MENTION_NOT_LIVE_INVITATION",d.context_codes)
        self.assertNotIn("DIRECT_OPEN",d.context_codes)
        self.assertFalse(d.authorizes_effects)

    def test_disclosure_does_not_require_reciprocal_statement(self):
        d=self.decide(act="DISCLOSURE",message="SYNTHETIC statement offered to be heard.")
        self.assertIn("HEAR_WITHOUT_FORCED_RECIPROCATION",d.context_codes)
        self.assertNotIn("DIRECT_OPEN",d.context_codes)

if __name__=="__main__":
    unittest.main()