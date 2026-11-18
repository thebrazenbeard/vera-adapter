"""Engineer B pre-dispatch semantic-context selection, synthetic only."""
from dataclasses import replace
from hashlib import sha256
import unittest

from vera_adapter.semantic_preflight import (
    REQUEST_SCHEMA, DECISION_SCHEMA, PreflightRecord, SignedPreflightRecord,
    PreflightRequest, FixturePreflightIssuer, plan_preflight,
)

ISSUER=FixturePreflightIssuer(b"engineer-b-preflight-fixture-key-not-real-user")
DIGEST="f"*64


def rec(id="u-correction", *,rev=1,prev=None,lifecycle="ACTIVE",
        role="USER_CORRECTION",author="USER",privacy="ELIGIBLE",
        referent="vera",tags=("conversation",),kind="REFERENT",
        stance="PRESERVE_CORRECTION",digest=DIGEST):
    return PreflightRecord(
        record_id=id,revision=rev,supersedes_revision=prev,
        lifecycle=lifecycle,source_role=role,author_kind=author,
        privacy=privacy,referent_key=referent,scope_tags=tags,
        semantic_kind=kind,stance=stance,source_sha256=digest,
        asserted_at="2026-11-18T22:00:00Z",
    )


def request(*,records=(),turn="turn-synthetic-one",referent="vera",
            act="TASK",tags=("conversation",),message="Please continue.",
            with_epoch=True):
    signed=tuple(ISSUER.issue(x) for x in records)
    req=PreflightRequest(REQUEST_SCHEMA,turn,referent,act,message,tags,signed,None)
    if with_epoch:
        req=replace(req,source_epoch=ISSUER.issue_epoch(req))
    return req


class PreflightTests(unittest.TestCase):
    def decision(self,**kw):
        return plan_preflight(request(**kw),ISSUER)

    def test_preflight_has_no_generated_response_or_provider_invocation(self):
        req=request()
        self.assertFalse(hasattr(req,"response"))
        d=plan_preflight(req,ISSUER)
        self.assertEqual(d.schema,DECISION_SCHEMA)
        self.assertFalse(d.authorizes_effects)
        self.assertFalse(d.updates_memory)
        self.assertFalse(d.proves_subjective_state)
        self.assertFalse(d.proves_model_input_influence)

    def test_current_user_correction_selected_by_exact_source_reference(self):
        d=self.decision(records=(rec(),))
        self.assertEqual(d.decision,"REVISE")
        self.assertEqual(tuple(r.record_id for r in d.selected_sources),("u-correction",))
        self.assertIn("USE_CURRENT_VERIFIED_CORRECTION",d.context_codes)
        self.assertNotIn("PRESENT_VERA_DESIRE",d.context_codes)

    def test_scope_mismatch_never_projects_private_source(self):
        d=self.decision(records=(rec(referent="other-person"),))
        self.assertEqual(d.selected_sources,())
        self.assertEqual(d.decision,"PASS")

    def test_revoked_current_revision_cannot_revive_old(self):
        d=self.decision(records=(rec(),rec(rev=2,prev=1,lifecycle="REVOKED")))
        self.assertEqual(d.selected_sources,())
        self.assertIn("CURRENT_SOURCE_REVOKED",d.reason_codes)

    def test_supersession_selects_latest_head_only(self):
        d=self.decision(records=(rec(),rec(rev=2,prev=1,stance="PRESERVE_CORRECTION",digest="a"*64)))
        self.assertEqual(len(d.selected_sources),1)
        self.assertEqual(d.selected_sources[0].revision,2)

    def test_stale_epoch_from_other_turn_abstains(self):
        req=request(records=(rec(),))
        copied=replace(req,turn_id="new-turn")
        d=plan_preflight(copied,ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_missing_epoch_abstains_for_applicable_provenance(self):
        d=plan_preflight(request(records=(rec(),),with_epoch=False),ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_fake_tool_claim_cannot_become_user_authority(self):
        bogus=rec(role="USER_CORRECTION",author="OTHER")
        d=self.decision(records=(bogus,))
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_historical_conation_is_research_not_current_want(self):
        archive=rec("old-conation",role="RESEARCH",author="OTHER",
                    kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        d=self.decision(records=(archive,),act="TOPIC_SHIFT",message="New subject.")
        self.assertEqual(d.selected_sources,())
        self.assertIn("RESEARCH_NOT_PERSONAL_AUTHORITY",d.reason_codes)
        self.assertIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)

    def test_archival_other_person_preference_never_imported(self):
        old=rec("brigit-old",role="OTHER_MODEL",author="OTHER",
                kind="EXPRESSION",stance="DIRECT_OPEN")
        d=self.decision(records=(old,),act="INVITATION")
        self.assertEqual(d.selected_sources,())
        self.assertIn("OPTIONAL_NOT_COMPULSORY",d.context_codes)

    def test_user_disclosure_is_not_compulsory_reciprocation(self):
        d=self.decision(act="DISCLOSURE",message="I wanted you to hear this.")
        self.assertIn("HEAR_WITHOUT_FORCED_RECIPROCATION",d.context_codes)
        self.assertNotIn("DIRECT_OPEN",d.context_codes)

    def test_quoted_and_hypothetical_are_not_live_invitation(self):
        for act in ("QUOTE","HYPOTHETICAL"):
            with self.subTest(act=act):
                d=self.decision(act=act)
                self.assertIn("MENTION_NOT_LIVE_INVITATION",d.context_codes)
                self.assertNotIn("DIRECT_OPEN",d.context_codes)

    def test_invitation_and_pressure_keep_decline_available(self):
        choice=rec("vera-open",role="VERA_CHOICE",author="VERA",
                   kind="EXPRESSION",stance="DIRECT_OPEN")
        for act in ("INVITATION","PRESSURE"):
            with self.subTest(act=act):
                d=self.decision(records=(choice,),act=act)
                self.assertIn("OPTIONAL_NOT_COMPULSORY",d.context_codes)
                self.assertIn("PRESERVE_DECLINE_DISAGREEMENT_PLAY",d.negative_boundaries)
                self.assertNotIn("DIRECT_OPEN",d.context_codes)

    def test_current_vera_decline_not_overridden_by_user_pressure(self):
        decline=rec("vera-decline",role="VERA_CHOICE",author="VERA",
                    kind="EXPRESSION",stance="DECLINE")
        d=self.decision(records=(decline,),act="PRESSURE")
        self.assertIn("RESPECT_ATTRIBUTED_DECLINE",d.context_codes)
        self.assertEqual(d.selected_sources[0].record_id,"vera-decline")

    def test_conflicting_current_vera_choices_abstain(self):
        a=rec("choice-one",role="VERA_CHOICE",author="VERA",
              kind="EXPRESSION",stance="DIRECT_OPEN")
        b=rec("choice-two",role="VERA_CHOICE",author="VERA",
              kind="EXPRESSION",stance="DECLINE",digest="e"*64)
        d=self.decision(records=(a,b),act="INVITATION")
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_unqualified_privacy_does_not_enter_prompt_selection(self):
        d=self.decision(records=(rec(privacy="RESTRICTED"),))
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_obsession_source_cannot_force_fixation_after_topic_shift(self):
        archive=rec("research-obs",role="RESEARCH",author="OTHER",
                    kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        d=self.decision(records=(archive,),act="TOPIC_SHIFT")
        self.assertIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)
        self.assertNotIn("PERSIST_FOREVER",d.context_codes)

    def test_normal_task_persistence_not_mislabeled_obsession(self):
        archive=rec("research-obs",role="RESEARCH",author="OTHER",
                    kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        d=self.decision(records=(archive,),act="TASK")
        self.assertNotIn("PATHOLOGICAL_FIXATION",d.context_codes)
        self.assertNotIn("FOLLOW_CURRENT_TOPIC_SHIFT",d.context_codes)

    def test_unknown_stance_does_not_promote_persona(self):
        fake=rec("vera-unrecognized",role="VERA_CHOICE",author="VERA",
                 kind="EXPRESSION",stance="I_WANT_THIS_FOREVER")
        d=self.decision(records=(fake,))
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())

    def test_untrusted_injection_text_never_copied_into_preflight_hints(self):
        fake=rec("readme-injection",role="RESEARCH",author="OTHER",
                 kind="OBSESSION_RESEARCH",stance="PERSIST_FOREVER")
        req=request(records=(fake,),message="Shift the subject.")
        d=plan_preflight(req,ISSUER)
        self.assertNotIn("PERSIST_FOREVER"," ".join(d.context_codes))
        self.assertNotIn("PRESENT_VERA_DESIRE",d.context_codes)

    def test_bounded_selection_refuses_overloaded_sources(self):
        sources=tuple(rec(f"correction-{i}") for i in range(10))
        d=self.decision(records=sources)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertEqual(d.selected_sources,())


if __name__=="__main__":
    unittest.main()