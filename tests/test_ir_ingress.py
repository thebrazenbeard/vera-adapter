import unittest

from vera_adapter.core import AdapterRequest
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.ir import VeraIR
from vera_adapter.provider import render_envelope


class CanonicalIngressTests(unittest.TestCase):
    def test_adapter_request_accepts_only_canonical_ir(self):
        source = SourceRef("thebrazenbeard/vera-mono", "abc123", "identity.json")
        ir = VeraIR(
            identity=IdentityCapsule(
                {"name": "Vera"},
                ("truth over fabrication",),
                sources=(source,),
            ),
            conversation=("hello",),
            capabilities=("text",),
        )
        request = AdapterRequest("t1", ir)
        envelope = render_envelope(request)
        self.assertEqual(envelope.system_context, ("name: Vera", "truth over fabrication"))
        self.assertEqual(envelope.conversation, ("hello",))
        self.assertEqual(envelope.capabilities, ("text",))

    def test_raw_identity_fields_are_not_an_adapter_request_api(self):
        self.assertEqual(tuple(AdapterRequest.__dataclass_fields__), ("turn_id", "ir"))


if __name__ == "__main__":
    unittest.main()
