import unittest
from vera_adapter import AdapterRequest, AdapterResponse, validate_response

class ModelProvenanceInputTests(unittest.TestCase):
    def test_turn_id_must_be_exact_nonempty_string(self):
        for turn in (True, 1, None, "", " "):
            with self.subTest(turn=repr(turn)):
                req=AdapterRequest(turn, {}, (), ())
                with self.assertRaises(ValueError):
                    validate_response(req, AdapterResponse(turn, "answer", "provider", "model"))

    def test_provider_and_model_must_not_be_coerced_from_scalars(self):
        req=AdapterRequest("turn-a", {}, (), ())
        for provider,model in ((True,"model"),(1,"model"),("provider",False),("provider",4)):
            with self.subTest(provenance=(provider,model)):
                with self.assertRaises(ValueError):
                    validate_response(req, AdapterResponse("turn-a", "answer", provider, model))
