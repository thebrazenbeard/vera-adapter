from dataclasses import asdict
from pathlib import Path
import json
import unittest
from vera_adapter.semantic_correction import DECISION_SCHEMA, SCHEMA
from tests.test_semantic_correction import VERIFIER, request
from vera_adapter.semantic_correction import review_candidate


class SemanticSchemaTests(unittest.TestCase):
    def test_checked_in_schemas_match_actual_review_envelopes(self):
        p=Path(__file__).resolve().parents[1]/"schemas"
        incoming=json.loads((p/"VERA_SEMANTIC_REVIEW_REQUEST_V1.schema.json").read_text())
        outgoing=json.loads((p/"VERA_SEMANTIC_REVIEW_DECISION_V1.schema.json").read_text())
        self.assertEqual(incoming["properties"]["schema"]["const"],SCHEMA)
        self.assertEqual(outgoing["properties"]["schema"]["const"],DECISION_SCHEMA)
        self.assertEqual(incoming["additionalProperties"],False)
        self.assertEqual(outgoing["additionalProperties"],False)
        x=asdict(request())
        y=asdict(review_candidate(request(),VERIFIER))
        self.assertEqual(set(x),set(incoming["properties"]))
        self.assertEqual(set(y),set(outgoing["properties"]))
        self.assertEqual(y["authorizes_effects"],False)
        self.assertEqual(y["updates_memory"],False)

    def test_rule_contract_explicitly_has_original_corrected_referent_and_source(self):
        p=Path(__file__).resolve().parents[1]/"schemas"/"VERA_SEMANTIC_REVIEW_REQUEST_V1.schema.json"
        schema=json.loads(p.read_text())
        required=set(schema["$defs"]["correction_rule"]["required"])
        for field in ("original","corrected","referent","scope_tags","scope_referent",
                      "source_sha256","authority_kind","privacy","lifecycle",
                      "revision","supersedes_revision","authored_at"):
            self.assertIn(field,required)


if __name__=="__main__":unittest.main()
