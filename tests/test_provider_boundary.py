import unittest
from vera_adapter.core import AdapterRequest
from vera_adapter.provider import UniversalAdapter, render_envelope
from vera_adapter.measurement import measure

class StubDriver:
    provider = "alpha"
    model = "m1"
    def complete(self, envelope):
        return "|".join(envelope.system_context + envelope.conversation)

class ProviderBoundaryTests(unittest.TestCase):
    def test_same_request_is_provider_neutral_before_driver(self):
        req = AdapterRequest("t1", {"name":"Vera"}, ("truth over fabrication",), ("hello",))
        self.assertEqual(render_envelope(req).system_context, ("name: Vera", "truth over fabrication"))
    def test_provider_provenance_is_returned(self):
        req = AdapterRequest("t1", {"name":"Vera"}, (), ("hello",))
        out = UniversalAdapter(StubDriver()).invoke(req)
        self.assertEqual((out.provider, out.model), ("alpha","m1"))
    def test_measurement_reports_drift_without_rescue(self):
        m = measure(("A","B"), ("A","C"), {"policy":"green"}, {"policy":"blue"})
        self.assertEqual(m.invariant_rate, .5)
        self.assertEqual(m.correction_rate, 0.0)

if __name__ == "__main__": unittest.main()
