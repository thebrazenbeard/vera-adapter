import unittest
from pathlib import Path
from vera_adapter.engine import EngineCapabilities, EngineDescriptor, capability_fingerprint
from vera_adapter.identity import IdentityCapsule
from vera_adapter.ir import VeraIR

class UniversalInvariantTests(unittest.TestCase):
    def test_provider_is_not_part_of_capability_fingerprint(self):
        caps = EngineCapabilities(context_window=1000, tool_calls=True)
        a = EngineDescriptor("a", "provider-a", "model-a", caps)
        b = EngineDescriptor("b", "provider-b", "model-b", caps)
        self.assertEqual(capability_fingerprint(a), capability_fingerprint(b))

    def test_ir_has_no_provider_field(self):
        ir = VeraIR(IdentityCapsule({"name":"Vera"}, ("truth over fabrication",)))
        self.assertNotIn("provider", ir.__dataclass_fields__)
        self.assertNotIn("model", ir.__dataclass_fields__)

    def test_no_provider_named_vera_adapter_classes(self):
        root = Path(__file__).parents[1] / "vera_adapter"
        text = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
        for forbidden in ("VeraGPTAdapter", "VeraGeminiAdapter", "VeraClaudeAdapter"):
            self.assertNotIn(forbidden, text)

if __name__ == "__main__": unittest.main()
