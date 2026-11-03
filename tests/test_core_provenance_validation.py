"""Fail-closed provenance checks for the model-neutral response envelope."""

import unittest
from types import SimpleNamespace

from vera_adapter import AdapterRequest, AdapterResponse, validate_response


class ModelProvenanceValidationTests(unittest.TestCase):
    def setUp(self):
        self.request = AdapterRequest("turn-1", {}, (), ())

    def test_blank_provider_or_model_cannot_be_validated_as_provenance(self):
        for provider, model in ((" ", "model"), ("provider", "\t"),
                                ("\n", "\r")):
            with self.subTest(provider=repr(provider), model=repr(model)):
                with self.assertRaisesRegex(ValueError, "provenance"):
                    validate_response(self.request,
                        AdapterResponse("turn-1", "text", provider, model))

    def test_nonstring_provenance_cannot_be_validated(self):
        for provider, model in ((1, "model"), ("provider", object()),
                                (True, "model")):
            with self.subTest(provider=repr(provider), model=repr(model)):
                with self.assertRaisesRegex(ValueError, "provenance"):
                    validate_response(self.request,
                        AdapterResponse("turn-1", "text", provider, model))

    def test_invisible_control_or_oversized_model_identity_claims_rejected(self):
        deceptive = ("\u200b", "\u200d", "\u2060", "\ufeff", "\u202e",
                     "\x00", "\x1b", "\ud800", "model" + "x" * 100_000)
        for value in deceptive:
            for field in ("provider", "model"):
                with self.subTest(field=field, sample=repr(value[:12])):
                    response = AdapterResponse("turn-1", "text", "provider", "model")
                    response = AdapterResponse(
                        response.turn_id, response.text,
                        value if field == "provider" else response.provider,
                        value if field == "model" else response.model,
                    )
                    with self.assertRaisesRegex(ValueError, "provenance"):
                        validate_response(self.request, response)

    def test_untyped_response_cannot_spoof_validated_envelope(self):
        spoof = SimpleNamespace(turn_id="turn-1", text="fabricated",
                                provider="provider", model="model",
                                proposed_actions=())
        with self.assertRaises(TypeError):
            validate_response(self.request, spoof)

    def test_output_and_proposed_actions_have_exact_wire_shapes(self):
        for text, proposals in ((object(), ()), ("text", ["proposal"]),
                                ("text", (42,)), ("text", (" ",))):
            with self.subTest(text_type=type(text).__name__, proposals=repr(proposals)):
                with self.assertRaisesRegex(ValueError, "response envelope"):
                    validate_response(self.request,
                        AdapterResponse("turn-1", text, "provider", "model", proposals))

        # A proposal may be returned, but this validator never executes it.
        response = AdapterResponse("turn-1", "text", "provider", "model",
                                   ("request_authorization_for_tool",))
        self.assertIs(validate_response(self.request, response), response)

    def test_blank_or_untyped_turn_identity_rejected(self):
        for turn_id in (" ", "\t", 1, True, "\u200b", "\u202e", "\x00",
                        "\x1b", "\ud800", "t" * 100_000):
            sample = repr(turn_id[:12]) if type(turn_id) is str else repr(turn_id)
            with self.subTest(turn_id=sample):
                with self.assertRaisesRegex(ValueError, "turn identity"):
                    validate_response(AdapterRequest(turn_id, {}, (), ()),
                        AdapterResponse(turn_id, "text", "provider", "model"))

    def test_backend_names_remain_unrestricted_model_neutral_strings(self):
        for provider, model in (("KoboldCPP", "Qwen3.5-4B.Q4_K_M.gguf"),
                                ("Ollama", "qwen3.5:4b"),
                                ("llama.cpp", "local/my-model"),
                                ("Local provider", "môdèle-語言/テスト")):
            with self.subTest(provider=provider):
                response = AdapterResponse("turn-1", "text", provider, model)
                self.assertIs(validate_response(self.request, response), response)


if __name__ == "__main__":
    unittest.main()
