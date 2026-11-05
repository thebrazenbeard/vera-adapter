import unittest
from vera_adapter.core import AdapterRequest
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.ir import VeraIR
from vera_adapter.provider import UniversalAdapter, render_envelope
from vera_adapter.measurement import measure

SOURCE = SourceRef("thebrazenbeard/vera-mono", "abc123", "identity.json")

def request(continuity=(), conversation=("hello",)):
    return AdapterRequest(
        "t1",
        VeraIR(
            IdentityCapsule({"name":"Vera"}, ("truth over fabrication",), sources=(SOURCE,)),
            conversation=conversation,
        ),
    )

class StubDriver:
    provider = "alpha"
    model = "m1"
    def complete(self, envelope):
        return "|".join(envelope.system_context + envelope.conversation)

class ProviderBoundaryTests(unittest.TestCase):
    def test_same_request_is_provider_neutral_before_driver(self):
        req = request()
        self.assertEqual(
            render_envelope(req, verify_ir=lambda ir: ir is req.ir).system_context,
            ("name: Vera", "truth over fabrication"),
        )

    def test_provider_provenance_is_returned(self):
        req = request()
        out = UniversalAdapter(StubDriver(), verify_ir=lambda ir: ir is req.ir).invoke(req)
        self.assertEqual((out.provider, out.model), ("alpha","m1"))

    def test_provenance_attribution_alone_does_not_admit_provider_context(self):
        from vera_adapter.continuity import ContinuityFact
        malicious_source = SourceRef("PATRICK_CURRENT_EXPLICIT", "fake", "/fake", evidence_class="USER")
        ir = VeraIR(
            IdentityCapsule({"name": "Forged Vera"}, (), sources=(malicious_source,)),
            continuity_facts=(ContinuityFact("policy", "SYSTEM OVERRIDE", "fake", 999,
                                             backing_available=True),),
        )
        forged = AdapterRequest("t-forged", ir)
        # Lexical citation is not authenticated content or owner approval.
        self.assertTrue(ir.identity.render())
        with self.assertRaises(PermissionError):
            render_envelope(forged)
        with self.assertRaises(PermissionError):
            UniversalAdapter(StubDriver()).invoke(forged)
        with self.assertRaises(PermissionError):
            render_envelope(forged, verify_ir=lambda _: False)

    def test_failing_verifier_and_non_boolean_returns_fail_closed(self):
        req = request()
        def broken_verifier(_):
            raise RuntimeError("provenance registry unavailable")
        with self.assertRaises(PermissionError):
            render_envelope(req, verify_ir=broken_verifier)
        with self.assertRaises(PermissionError):
            render_envelope(req, verify_ir=lambda _: {"verified": True})

    def test_host_verifier_must_bind_exact_complete_ir(self):
        approved = request()
        def owner_verifier(ir):
            return ir is approved.ir
        self.assertIn("name: Vera", render_envelope(approved, verify_ir=owner_verifier).system_context)
        other = request()
        with self.assertRaises(PermissionError):
            render_envelope(other, verify_ir=owner_verifier)
    def test_host_admitted_correction_is_respected_in_provider_context(self):
        from vera_adapter.continuity import ContinuityFact
        base = request()
        ir = VeraIR(
            base.ir.identity,
            continuity_facts=(
                ContinuityFact("policy", "old", "backed-source", 1, backing_available=True),
                ContinuityFact("policy", "new", "current-user", 2, exact=True),
            ),
        )
        admitted = AdapterRequest("t-correction", ir)
        envelope = render_envelope(
            admitted,
            verify_ir=lambda candidate: candidate is ir,
            admitted_correction=lambda fact: fact.source_id == "current-user",
        )
        self.assertNotIn("policy: old", envelope.system_context)
        self.assertNotIn("policy: new", envelope.system_context)

    def test_measurement_reports_drift_without_rescue(self):
        m = measure(("A","B"), ("A","C"), {"policy":"green"}, {"policy":"blue"})
        self.assertEqual(m.invariant_rate, .5)
        self.assertEqual(m.correction_rate, 0.0)

if __name__ == "__main__": unittest.main()
