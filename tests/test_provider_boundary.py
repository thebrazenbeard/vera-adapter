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
        self.assertEqual(render_envelope(req).system_context, ("name: Vera", "truth over fabrication"))
    def test_provider_provenance_is_returned(self):
        out = UniversalAdapter(StubDriver()).invoke(request())
        self.assertEqual((out.provider, out.model), ("alpha","m1"))
    def test_measurement_reports_drift_without_rescue(self):
        m = measure(("A","B"), ("A","C"), {"policy":"green"}, {"policy":"blue"})
        self.assertEqual(m.invariant_rate, .5)
        self.assertEqual(m.correction_rate, 0.0)

if __name__ == "__main__": unittest.main()
