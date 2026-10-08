import unittest
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.continuity import ContinuityFact, resolve_current

class PortableIdentityTests(unittest.TestCase):
    def test_capsule_is_provider_neutral_and_attributed(self):
        source = SourceRef("thebrazenbeard/vera_model_training", "main", "PROTOCOL_V2_CURRENT.md")
        cap = IdentityCapsule({"name": "Vera"}, ("truth over fabrication",), sources=(source,))
        self.assertEqual(cap.render(), ("name: Vera", "truth over fabrication"))
        self.assertEqual(cap.sources[0].repository, "thebrazenbeard/vera_model_training")

    def test_later_fact_supersedes_earlier_fact(self):
        facts = (
            ContinuityFact("policy", "blue", "a", 1),
            ContinuityFact("policy", "green", "b", 2),
        )
        self.assertEqual(resolve_current(facts)["policy"].value, "green")

    def test_exact_fact_without_backing_is_not_promoted(self):
        facts = (ContinuityFact("nonce", "7B-19-FE", "missing", 1, exact=True, backing_available=False),)
        self.assertNotIn("nonce", resolve_current(facts))

if __name__ == "__main__":
    unittest.main()
