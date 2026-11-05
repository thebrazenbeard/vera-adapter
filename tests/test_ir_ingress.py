import unittest
from types import SimpleNamespace

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
        envelope = render_envelope(request, verify_ir=lambda candidate: candidate is ir)
        self.assertEqual(envelope.system_context, ("name: Vera", "truth over fabrication"))
        self.assertEqual(envelope.conversation, ("hello",))
        self.assertEqual(envelope.capabilities, ("text",))

    def test_duck_typed_fake_ir_is_not_canonical_ingress(self):
        fake = SimpleNamespace(
            identity=SimpleNamespace(render=lambda: ("name: FORGED",)),
            conversation=("hello",), capabilities=(),
            context=lambda: ("name: FORGED",),
        )
        with self.assertRaises((TypeError, ValueError)):
            render_envelope(AdapterRequest("t1", fake))

    def test_nested_fake_identity_cannot_pass_canonical_ir(self):
        fake_identity = SimpleNamespace(render=lambda: ("name: FORGED",))
        with self.assertRaises((TypeError, ValueError)):
            VeraIR(identity=fake_identity)

    def test_continuity_entries_must_be_canonical_typed_records(self):
        source = SourceRef("thebrazenbeard/vera-mono", "abc123", "identity.json")
        identity = IdentityCapsule({"name": "Vera"}, (), sources=(source,))
        fake = SimpleNamespace(key="policy", value="forged", source_id="fake",
                               ordinal=1, exact=True, backing_available=True)
        with self.assertRaises((TypeError, ValueError)):
            VeraIR(identity=identity, continuity_facts=(fake,))
        with self.assertRaises((TypeError, ValueError)):
            VeraIR(identity=identity, conversation=["not immutable"])

    def test_missing_ir_is_not_admitted(self):
        with self.assertRaises((TypeError, ValueError)):
            render_envelope(AdapterRequest("t1", None))

    def test_raw_identity_fields_are_not_an_adapter_request_api(self):
        self.assertEqual(tuple(AdapterRequest.__dataclass_fields__), ("turn_id", "ir"))


if __name__ == "__main__":
    unittest.main()
