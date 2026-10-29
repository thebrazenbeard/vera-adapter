import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from continuity_state import ContinuityError, apply_candidate_change


BASE = {"version": 0, "changes": []}
IMPORT = {
    "change_id": "import-001",
    "target": "historical_evidence:book_title",
    "change_class": "historical_evidence_import",
    "state_family": "MEMORY_STATE",
    "origin": "historical_import",
    "authority": "explicit_user_import",
    "prior_version": 0,
    "successor_version": 1,
    "trigger": "user-imported reference",
    "timestamp": "2026-10-29T00:00:00Z",
    "evidence_refs": ["example-source:1"],
    "continuity_effect": "record_evidence_only",
    "first_person_experience": False,
}


class ContinuityStateTests(unittest.TestCase):
    def test_historical_import_stays_evidence(self):
        next_state = apply_candidate_change(BASE, IMPORT)
        self.assertEqual(next_state["version"], 1)
        self.assertEqual(next_state["changes"][0]["continuity_effect"], "record_evidence_only")
        self.assertEqual(BASE, {"version": 0, "changes": []})

    def test_no_first_person_promotion(self):
        with self.assertRaisesRegex(ContinuityError, "first-person"):
            apply_candidate_change(BASE, dict(IMPORT, first_person_experience=True))

    def test_no_stale_write(self):
        with self.assertRaisesRegex(ContinuityError, "stale"):
            apply_candidate_change(BASE, dict(IMPORT, prior_version=1))

    def test_no_identity_critical_write(self):
        with self.assertRaisesRegex(ContinuityError, "separate authority"):
            apply_candidate_change(BASE, dict(IMPORT, change_class="self_model_change"))

    def test_no_identity_target_via_historical_import(self):
        with self.assertRaisesRegex(ContinuityError, "class-scoped namespace"):
            apply_candidate_change(BASE, dict(IMPORT, target="identity_critical:Vera"))

    def test_no_historical_target_via_preference(self):
        with self.assertRaisesRegex(ContinuityError, "class-scoped namespace"):
            apply_candidate_change(BASE, dict(IMPORT, change_class="user_preference",
                                              state_family="CONFIGURABLE_STATE",
                                              origin="user_owned", authority="explicit_user_instruction"))

    def test_no_skill_auto_install(self):
        candidate = dict(IMPORT, change_class="evaluated_skill_candidate", state_family="PLASTIC_STATE",
                         origin="training_artifact", authority="heldout_evaluation",
                         target="skill_candidate:basic_arithmetic",
                         evidence_refs=["baseline:1", "heldout:1"], continuity_effect="auto_install")
        with self.assertRaisesRegex(ContinuityError, "auto-install"):
            apply_candidate_change(BASE, candidate)

    def test_no_single_evidence_skill(self):
        candidate = dict(IMPORT, change_class="evaluated_skill_candidate", state_family="PLASTIC_STATE",
                         origin="training_artifact", authority="heldout_evaluation",
                         target="skill_candidate:basic_arithmetic",
                         evidence_refs=["heldout:1"], continuity_effect="candidate_only")
        with self.assertRaisesRegex(ContinuityError, "baseline"):
            apply_candidate_change(BASE, candidate)

    def test_no_duplicate_record(self):
        next_state = apply_candidate_change(BASE, IMPORT)
        changed_version = dict(IMPORT, prior_version=1, successor_version=2)
        with self.assertRaisesRegex(ContinuityError, "unique"):
            apply_candidate_change(next_state, changed_version)


if __name__ == "__main__":
    unittest.main()
