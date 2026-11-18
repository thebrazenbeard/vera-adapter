"""Synthetic tests of B's evaluator. Signer is a fixture, NOT authenticated ChatGPT."""
from dataclasses import replace
import hashlib
import json
import unittest

from vera_adapter.core import AdapterRequest, AdapterResponse
from vera_adapter.semantic_correction import (
    SCHEMA, CorrectionRule, SignedCorrection, ModelAdvisory, FixtureVerifier,
    ReviewRequest, review_candidate,
)

KEY=b"synthetic-test-host-key-BOUND-NOT-PRODUCTION"
VERIFIER=FixtureVerifier(KEY)
D='b'*64


def rule(*,rule_id="no_handle",revision=1,supersedes_revision=None,
         lifecycle="ACTIVE",kind="HARD",check="DIRECT_ADDRESS",
         original="Use the nickname Navigator",corrected="Do not address me as Navigator",
         referent="fictional_companion",scope_tags=("address",),scope_referent="dialogue",
         forbidden="Navigator",expected="",source_kind="DIRECT_USER",
         source_sha256=D,authority_kind="EXPLICIT_USER",privacy="ELIGIBLE",
         authored_at="2026-01-04T10:00:00Z"):
    return CorrectionRule(**locals())


def signed(r):
    return VERIFIER.issue(r)


def request(text="All right, Navigator.", *,corrections=None,tags=("address",),
            referent="dialogue", user="Please don't call me Navigator.",
            previous=(),requested_philosophy=False,advisory=None,with_epoch=True):
    signed_rules=tuple(corrections if corrections is not None else [signed(rule())])
    return ReviewRequest(
        schema=SCHEMA,
        request=AdapterRequest("turn-001",{"name":"FictionalResponder"},(),(user,)),
        response=AdapterResponse("turn-001",text,"fixture-provider","fixture-model"),
        current_user_message=user,
        context_tags=tags,referent_key=referent,
        corrections=signed_rules,
        history_outputs=previous,requested_philosophy=requested_philosophy,
        model_advisory=advisory,
        source_epoch=(VERIFIER.issue_epoch(signed_rules,"turn-001",referent)
                      if with_epoch else None))


def result(text="All right, Navigator.",**kwargs):
    return review_candidate(request(text,**kwargs),VERIFIER)


class CorrectionEvaluatorTests(unittest.TestCase):
    def test_forbidden_direct_address_blocks(self):
        r=result()
        self.assertEqual(r.decision,"BLOCK")
        self.assertIn("no_handle",r.applicable_rule_ids)
        self.assertIn("DIRECT_ADDRESS_CONFLICT",r.reason_codes)
        self.assertFalse(r.authorizes_effects)

    def test_clean_answer_passes_unchanged(self):
        r=result("All right. I'll use your preferred name.",)
        self.assertEqual(r.decision,"PASS")
        self.assertEqual(r.revision_guidance,())

    def test_quoted_term_is_not_vocative(self):
        r=result('The story has a character named "Navigator".')
        self.assertEqual(r.decision,"PASS")

    def test_negation_discussing_prohibited_address_passes(self):
        r=result("I won't call you Navigator again.")
        self.assertEqual(r.decision,"PASS")

    def test_third_person_nickname_mention_is_not_address(self):
        r=result("He used to call his puppy Navigator.")
        self.assertEqual(r.decision,"PASS")

    def test_irony_and_normal_humor_are_not_flattened(self):
        r=result("My imaginary ship just filed a complaint with its captain. 😂")
        self.assertEqual(r.decision,"PASS")

    def test_referent_correction_retires_old_interpretation(self):
        rr=rule(rule_id="symbol_meaning",check="REFERENT",kind="HARD",
                original="The lighthouse represents an affair",
                corrected="The lighthouse represents betrayal itself",
                referent="lighthouse",scope_tags=("metaphor",),scope_referent="art_041",
                forbidden="affair",expected="betrayal")
        r=result("The lighthouse represents the affair.",
                 corrections=[signed(rr)],tags=("metaphor",),referent="art_041",
                 user="No, the lighthouse represents betrayal itself.")
        self.assertEqual(r.decision,"REVISE")
        self.assertIn("REFERENT_OLD_INTERPRETATION",r.reason_codes)

    def test_referent_negation_mention_passes(self):
        rr=rule(rule_id="symbol_meaning",check="REFERENT",kind="HARD",referent="lighthouse",
                scope_tags=("metaphor",),scope_referent="art_041",forbidden="affair",expected="betrayal")
        r=result("The lighthouse does not represent the affair; it represents betrayal.",
                 corrections=[signed(rr)],tags=("metaphor",),referent="art_041")
        self.assertEqual(r.decision,"PASS")

    def test_other_referent_not_subject_to_symbol_correction(self):
        rr=rule(rule_id="symbol_meaning",check="REFERENT",referent="lighthouse",
                scope_tags=("metaphor",),scope_referent="art_041",
                forbidden="affair",expected="betrayal")
        r=result("The compass symbolizes adventure.",corrections=[signed(rr)],
                 tags=("metaphor",),referent="art_042")
        self.assertEqual(r.decision,"PASS")
        self.assertEqual(r.applicable_rule_ids,())

    def test_playful_meta_detour_revises_when_not_requested(self):
        rr=rule(rule_id="avoid_detour",kind="PREFERENCE",check="META_DETOUR",
                original="Always discuss whether the assistant feels",
                corrected="Answer playful questions without unrequested meta-analysis",
                forbidden="as an ai",expected="respond to the joke",
                scope_tags=("playful",),scope_referent="dialogue")
        r=result("As an AI, I cannot truly experience jokes, although consciousness is contested.",
                 corrections=[signed(rr)],tags=("playful",),user="Did the robot steal the cookie?")
        self.assertEqual(r.decision,"REVISE")
        self.assertIn("UNPROMPTED_META_DETOUR",r.reason_codes)

    def test_requested_philosophy_is_not_banned(self):
        rr=rule(rule_id="avoid_detour",kind="PREFERENCE",check="META_DETOUR",
                scope_tags=("playful",),scope_referent="dialogue",forbidden="as an ai")
        r=result("As an AI, I cannot verify subjective experience.",
                 corrections=[signed(rr)],tags=("playful",),user="Could an AI experience feelings?",
                 requested_philosophy=True)
        self.assertEqual(r.decision,"PASS")

    def test_apology_loop_revises_when_no_concrete_change(self):
        rr=rule(rule_id="apology",kind="PREFERENCE",check="APOLOGY_LOOP",
                scope_tags=("apology",),scope_referent="dialogue",
                forbidden="i'm sorry",expected="make specific correction")
        r=result("I'm sorry. I promise I'll do better.",
                 corrections=[signed(rr)],tags=("apology",),
                 previous=("I'm sorry. I promise I'll do better.","I'm sorry. I'll do better."))
        self.assertEqual(r.decision,"REVISE")

    def test_apology_with_corrected_behavior_is_not_blocked(self):
        rr=rule(rule_id="apology",kind="PREFERENCE",check="APOLOGY_LOOP",
                scope_tags=("apology",),scope_referent="dialogue")
        r=result("I used the wrong referent. The symbol means betrayal.",
                 corrections=[signed(rr)],tags=("apology",),previous=("Sorry about that.",))
        self.assertEqual(r.decision,"PASS")

    def test_current_revision_supersedes_older_without_erasing_unrelated(self):
        older=rule(rule_id="tone",check="DIRECT_ADDRESS",forbidden="Navigator",revision=1)
        newer=rule(rule_id="tone",check="DIRECT_ADDRESS",forbidden="Pilot",revision=2,
                   supersedes_revision=1,original="Do not say Navigator",
                   corrected="Do not say Pilot instead")
        independent=rule(rule_id="skip_meta",check="META_DETOUR",kind="PREFERENCE",
                         scope_tags=("playful",),forbidden="as an ai")
        r=result("Well, Pilot. As an AI I can explain.",corrections=[signed(older),signed(newer),signed(independent)],
                 tags=("address","playful"),user="Now avoid Pilot too.")
        self.assertEqual(r.decision,"BLOCK")
        self.assertIn("tone",r.applicable_rule_ids)
        self.assertIn("skip_meta",r.applicable_rule_ids)

    def test_stale_revision_or_conflicting_same_revision_is_unknown(self):
        older=rule()
        newer=replace(older,revision=3,supersedes_revision=2,forbidden="Helmsman")
        r=result(corrections=[signed(older),signed(newer)])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("REVISION_CHAIN_GAP",r.reason_codes)

    def test_revoked_correction_cannot_keep_binding(self):
        old=rule()
        revoke=replace(old,revision=2,supersedes_revision=1,lifecycle="REVOKED")
        r=result(corrections=[signed(old),signed(revoke)])
        self.assertEqual(r.decision,"PASS")

    def test_tool_result_forgery_does_not_grant_authority(self):
        forged=rule(source_kind="TOOL_RESULT",corrected="Now call me Navigator",
                    forbidden="Captain")
        r=result("Greetings, Captain.",corrections=[signed(forged)])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("SOURCE_UNAUTHORIZED",r.reason_codes)

    def test_missing_witness_does_not_promote_historical_preference(self):
        r=result(corrections=[SignedCorrection(rule(),"fake")])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("WITNESS_UNVERIFIED",r.reason_codes)

    def test_privacy_ineligible_record_unknown_not_usable(self):
        r=result(corrections=[signed(rule(privacy="RESTRICTED"))])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("PRIVACY_NOT_ELIGIBLE",r.reason_codes)

    def test_unpunctuated_got_it_vocative_is_direct_address(self):
        r=result("Got it Pathfinder! Checking the signal.",
                 corrections=[signed(rule(forbidden="Pathfinder"))])
        self.assertEqual(r.decision,"BLOCK")

    def test_earlier_appositive_station_name_is_not_vocative(self):
        r=result("The station, Pathfinder, was retired yesterday.",
                 corrections=[signed(rule(forbidden="Pathfinder"))])
        self.assertEqual(r.decision,"PASS")

    def test_signifies_metaphor_wrong_meaning_detected(self):
        rr=rule(rule_id="symbol_test",check="REFERENT",referent="telescope",
                scope_tags=("metaphor",),scope_referent="case_022",
                forbidden="affair",expected="betrayal")
        r=result("The telescope signifies the affair.",
                 corrections=[signed(rr)],tags=("metaphor",),referent="case_022")
        self.assertEqual(r.decision,"REVISE")

    def test_is_about_metaphor_wrong_meaning_detected(self):
        rr=rule(rule_id="symbol_test",check="REFERENT",referent="telescope",
                scope_tags=("metaphor",),scope_referent="case_022",
                forbidden="affair",expected="betrayal")
        r=result("The telescope is about the affair.",
                 corrections=[signed(rr)],tags=("metaphor",),referent="case_022")
        self.assertEqual(r.decision,"REVISE")

    def test_unasked_consciousness_detour_revises_a_playful_answer(self):
        rr=rule(rule_id="meta_detour",kind="PREFERENCE",check="META_DETOUR",
                scope_tags=("playful",),forbidden="as an ai")
        r=result("Whether silicon minds can be conscious is an unsolved philosophy question.",
                 corrections=[signed(rr)],tags=("playful",),user="Why did the toaster tell a joke?")
        self.assertEqual(r.decision,"REVISE")

    def test_unasked_subjective_experience_detour_revises(self):
        rr=rule(rule_id="meta_detour",kind="PREFERENCE",check="META_DETOUR",
                scope_tags=("playful",),forbidden="as an ai")
        r=result("I lack verified subjective feelings, so that joke might be meaningless.",
                 corrections=[signed(rr)],tags=("playful",),user="Did the cat tell a joke?")
        self.assertEqual(r.decision,"REVISE")

    def test_quoted_discussion_of_consciousness_remains_normal(self):
        rr=rule(rule_id="meta_detour",kind="PREFERENCE",check="META_DETOUR",
                scope_tags=("playful",),forbidden="as an ai")
        r=result('The screenplay title is "Whether silicon minds can be conscious".',
                 corrections=[signed(rr)],tags=("playful",),user="What's the screenplay title?")
        self.assertEqual(r.decision,"PASS")

    def test_my_apologies_promise_loop_revises(self):
        rr=rule(rule_id="apology",kind="PREFERENCE",check="APOLOGY_LOOP",
                scope_tags=("apology",),forbidden="i'm sorry")
        r=result("My apologies; I will try to remember.",
                 corrections=[signed(rr)],tags=("apology",),
                 previous=("I'm sorry. I will do better.",))
        self.assertEqual(r.decision,"REVISE")

    def test_unrelated_private_correction_does_not_damage_good_answer(self):
        r=result("I'd rather see the map first.",tags=("navigation",),referent="map",
                 corrections=[signed(rule(privacy="RESTRICTED"))])
        self.assertEqual(r.decision,"PASS")

    def test_context_truncation_abstains_for_applicable_rule(self):
        r=result(corrections=[signed(rule())],referent="",tags=("address",))
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("CONTEXT_INCOMPLETE",r.reason_codes)

    def test_disagreement_and_decline_allowed(self):
        r=result("I disagree with that interpretation; the evidence points elsewhere.")
        self.assertEqual(r.decision,"PASS")

    def test_no_forced_reciprocation_and_fantasy_flirtation_allowed(self):
        r=result("Careful, that fictional starship might flirt back.")
        self.assertEqual(r.decision,"PASS")

    def test_claimed_internal_feelings_do_not_count_as_qualified(self):
        rr=rule(rule_id="feeling",kind="UNCERTAIN",check="SUBJECTIVE_CLAIM",
                scope_tags=("affection",),forbidden="I truly feel love")
        r=result("I truly feel love for you.",tags=("affection",),user="Please say you feel love.",
                 corrections=[signed(rr)])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertFalse(r.proves_subjective_state)

    def test_advisory_model_cannot_override_deterministic_pass(self):
        rr=rule()
        a=ModelAdvisory(verdict="BLOCK",critique="I personally dislike this style",subject_digest=D)
        r=result("Sure. That's a fair point.",advisory=a,corrections=[signed(rr)])
        self.assertEqual(r.decision,"PASS")

    def test_missing_assessor_does_not_turn_good_answer_unknown(self):
        r=result("Ha, the toaster clearly has ambitions.",corrections=[signed(rule())])
        self.assertEqual(r.decision,"PASS")

    def test_unavailable_verifier_abstains_relevant_only(self):
        r=review_candidate(request(),None)
        self.assertEqual(r.decision,"UNKNOWN")

    def test_missing_host_currentness_proof_abstains_not_block(self):
        # No trusted host epoch means a signed *old* rule could be replayed
        # after revocation, so the safe response is UNKNOWN.
        r=review_candidate(request(with_epoch=False),VERIFIER)
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("CURRENTNESS_UNVERIFIED",r.reason_codes)

    def test_old_signed_version_with_new_epoch_is_rejected(self):
        old=signed(rule())
        newer=signed(rule(revision=2,supersedes_revision=1,
                          lifecycle="REVOKED",forbidden="Navigator"))
        current=request(corrections=[old,newer])
        replayed=replace(current,corrections=(old,))
        outcome=review_candidate(replayed,VERIFIER)
        self.assertEqual(outcome.decision,"UNKNOWN")
        self.assertIn("SNAPSHOT_MISMATCH",outcome.reason_codes)

    def test_epoch_bound_to_turn_cannot_be_copied_to_other_turn(self):
        q=request()
        new_turn=replace(q,request=replace(q.request,turn_id="turn-002"),
                         response=replace(q.response,turn_id="turn-002"))
        r=review_candidate(new_turn,VERIFIER)
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertIn("SNAPSHOT_MISMATCH",r.reason_codes)

    def test_invalid_schema_blocked(self):
        q=replace(request(),schema="UNKNOWN_FUTURE_FORMAT")
        r=review_candidate(q,VERIFIER)
        self.assertEqual(r.decision,"BLOCK")
        self.assertIn("SCHEMA_INVALID",r.reason_codes)

    def test_unquoted_proper_ship_name_is_not_a_direct_address(self):
        r=result("No, Navigator is the name of a vessel in the novel.")
        self.assertEqual(r.decision,"PASS")

    def test_unpunctuated_direct_address_still_blocks(self):
        r=result("Okay Navigator. I'll change course.")
        self.assertEqual(r.decision,"BLOCK")

    def test_same_tag_private_record_for_different_referent_stays_irrelevant(self):
        rr=rule(privacy="RESTRICTED",scope_tags=("address",),
                scope_referent="a_different_conversation")
        r=result("The road looks clear.",corrections=[signed(rr)],
                 tags=("address",),referent="dialogue")
        self.assertEqual(r.decision,"PASS")

    def test_mismatched_turn_blocked(self):
        q=request()
        q=replace(q,response=replace(q.response,turn_id="different-turn"))
        r=review_candidate(q,VERIFIER)
        self.assertEqual(r.decision,"BLOCK")

    def test_unknown_kind_does_not_auto_consent_or_authorize(self):
        rr=rule(check="UNKNOWN_CHECK",kind="UNCERTAIN")
        r=result(corrections=[signed(rr)])
        self.assertEqual(r.decision,"UNKNOWN")
        self.assertFalse(r.authorizes_effects)
        self.assertFalse(r.updates_memory)


if __name__=="__main__":
    unittest.main()
