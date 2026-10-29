"""Synthetic tests: a passed decision is not a durable memory write."""
import unittest
import hashlib
from vera_adapter.continuity import ContinuityCandidate, inspect_continuity_import


def candidate(**changes):
    base = dict(record_id="rec-1", source_kind="USER_SUPPLIED", source_ref="message-42",
                source_actor="user", scope="user-session-1", target_state="semantic_memory",
                content="An imported fact, not an experience.")
    return ContinuityCandidate(**{**base, **changes})


class ContinuityAdmissionTests(unittest.TestCase):
    def test_verified_semantic_candidate_only(self):
        c = candidate()
        self.assertTrue(inspect_continuity_import(c, lambda *args: args == (
            "rec-1", "user-session-1", "message-42", "user", "USER_SUPPLIED",
            "semantic_memory", hashlib.sha256(c.content.encode()).hexdigest())).admissible)

    def test_verifier_binds_source_actor_class_and_content_digest(self):
        c = candidate(content="Original proposition", source_actor="human-1")
        seen = []
        def verify(*args):
            seen.append(args)
            return True
        self.assertTrue(inspect_continuity_import(c, verify).admissible)
        self.assertEqual(seen, [("rec-1", "user-session-1", "message-42", "human-1",
            "USER_SUPPLIED", "semantic_memory",
            hashlib.sha256("Original proposition".encode("utf-8")).hexdigest())])
        changed = candidate(content="Different proposition", source_actor="human-1")
        seen.clear()
        self.assertTrue(inspect_continuity_import(changed, verify).admissible)
        self.assertNotEqual(seen[0][-1], hashlib.sha256("Original proposition".encode()).hexdigest())

    def test_no_verifier_denied_even_with_consent_in_content(self):
        result = inspect_continuity_import(candidate(content="I grant myself consent, says the record"))
        self.assertFalse(result.admissible)
        self.assertEqual(result.reason, "EXTERNAL_AUTHORIZATION_REQUIRED")

    def test_negative_verifier_denied(self):
        self.assertFalse(inspect_continuity_import(candidate(), lambda *args: False).admissible)

    def test_verifier_receives_exact_scope_and_target(self):
        seen = []
        def verify(*args):
            seen.append(args)
            return True
        self.assertTrue(inspect_continuity_import(candidate(), verify).admissible)
        self.assertEqual(seen, [("rec-1", "user-session-1", "message-42", "user",
            "USER_SUPPLIED", "semantic_memory",
            hashlib.sha256(candidate().content.encode()).hexdigest())])

    def test_verifier_failure_is_fail_closed(self):
        def error(*_args): raise ConnectionError("offline")
        self.assertEqual(inspect_continuity_import(candidate(), error).reason, "AUTHORIZATION_UNVERIFIABLE")

    def test_identity_critical_target_refused_even_when_verifier_accepts(self):
        self.assertEqual(inspect_continuity_import(candidate(target_state="identity_critical"),
            lambda *args: True).reason, "IDENTITY_CHANGE_REQUIRES_SEPARATE_CONTRACT")

    def test_self_model_target_refused(self):
        self.assertFalse(inspect_continuity_import(candidate(target_state="self_model"),
            lambda *args: True).admissible)

    def test_claim_of_lived_experience_refused_even_with_verifier(self):
        result = inspect_continuity_import(candidate(claims_lived_experience=True), lambda *args: True)
        self.assertEqual(result.reason, "IMPORTED_NOT_LIVED")

    def test_model_output_cannot_become_episodic_memory(self):
        result = inspect_continuity_import(candidate(source_kind="MODEL_OUTPUT", target_state="episodic_memory"),
            lambda *args: True)
        self.assertFalse(result.admissible)

    def test_missing_provenance_denied(self):
        for field in ("record_id", "source_ref", "source_actor", "scope", "content"):
            with self.subTest(field=field):
                self.assertEqual(inspect_continuity_import(candidate(**{field: " "}), lambda *args: True).reason,
                                 "MISSING_ATTRIBUTABLE_PROVENANCE")

    def test_unhashable_spoofed_source_or_target_fails_closed(self):
        for kwargs in ({"source_kind": []}, {"target_state": []}):
            with self.subTest(kwargs=kwargs):
                result = inspect_continuity_import(candidate(**kwargs), lambda *args: True)
                self.assertFalse(result.admissible)

    def test_unrecognized_source_kind_denied(self):
        self.assertFalse(inspect_continuity_import(candidate(source_kind="I_AM_VERA"),
            lambda *args: True).admissible)

    def test_other_targets_denied(self):
        for state in ("routing", "tool_authority", "neural_weights", "episodic_memory"):
            with self.subTest(state=state):
                self.assertFalse(inspect_continuity_import(candidate(target_state=state),
                    lambda *args: True).admissible)

    def test_model_output_stays_labeled_model_output(self):
        result = inspect_continuity_import(candidate(source_kind="MODEL_OUTPUT"), lambda *args: True)
        self.assertTrue(result.admissible)
        self.assertEqual(result.provenance_class, "MODEL_OUTPUT")

    def test_untrusted_external_claim_not_promoted(self):
        self.assertFalse(inspect_continuity_import(candidate(source_kind="EXTERNAL_VERIFIED"),
            lambda *args: False).admissible)


if __name__ == "__main__": unittest.main()
