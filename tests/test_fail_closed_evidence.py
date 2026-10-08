import unittest

from vera_adapter.continuity import ContinuityFact, resolve_current
from vera_adapter.identity import IdentityCapsule, SourceRef


class FailClosedEvidenceTests(unittest.TestCase):
    def test_newer_unbacked_exact_correction_invalidates_older_value(self):
        facts = (
            ContinuityFact("policy", "blue", "old", 1),
            ContinuityFact("policy", "green", "new", 2, exact=True, backing_available=False),
        )
        self.assertNotIn("policy", resolve_current(facts))

    def test_exact_fact_is_fail_closed_by_default(self):
        fact = ContinuityFact("nonce", "7B-19-FE", "unchecked", 1, exact=True)
        self.assertFalse(fact.backing_available)
        self.assertNotIn("nonce", resolve_current((fact,)))

    def test_identity_render_rejects_missing_provenance(self):
        capsule = IdentityCapsule({"name": "Vera"}, ("truth over fabrication",))
        with self.assertRaises(ValueError):
            capsule.render()

    def test_identity_render_rejects_incomplete_provenance(self):
        capsule = IdentityCapsule(
            {"name": "Vera"},
            ("truth over fabrication",),
            sources=(SourceRef("", "main", "identity.json"),),
        )
        with self.assertRaises(ValueError):
            capsule.render()

    def test_identity_render_accepts_attributed_source(self):
        source = SourceRef("thebrazenbeard/vera-mono", "abc123", "identity.json")
        capsule = IdentityCapsule(
            {"name": "Vera"},
            ("truth over fabrication",),
            sources=(source,),
        )
        self.assertEqual(capsule.render(), ("name: Vera", "truth over fabrication"))


if __name__ == "__main__":
    unittest.main()
