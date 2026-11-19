"""Source-pinned preflight schema and hostile host-boundary tests."""
from dataclasses import asdict, replace
from pathlib import Path
import json
import unittest

from tests.test_semantic_preflight import ISSUER, rec, request
from vera_adapter.semantic_preflight import DECISION_SCHEMA, REQUEST_SCHEMA, plan_preflight


class PreflightContractTests(unittest.TestCase):
    def test_checked_in_schemas_match_public_envelopes(self):
        root=Path(__file__).resolve().parents[1]/"schemas"
        incoming=json.loads((root/(REQUEST_SCHEMA+".schema.json")).read_text(encoding="utf8"))
        outgoing=json.loads((root/(DECISION_SCHEMA+".schema.json")).read_text(encoding="utf8"))
        a=asdict(request(records=(rec(),)))
        b=asdict(plan_preflight(request(records=(rec(),)),ISSUER))
        for contract,data,name in ((incoming,a,REQUEST_SCHEMA),(outgoing,b,DECISION_SCHEMA)):
            self.assertFalse(contract["additionalProperties"])
            self.assertEqual(contract["properties"]["schema"]["const"],name)
            self.assertEqual(set(contract["required"]),set(data))
            self.assertEqual(set(contract["properties"]),set(data))
        for key in ("authorizes_effects","updates_memory","proves_subjective_state",
                    "proves_model_input_influence"):
            self.assertEqual(outgoing["properties"][key]["const"],False)
            self.assertFalse(b[key])

    def test_record_schema_has_ownership_currentness_and_privacy(self):
        path=Path(__file__).resolve().parents[1]/"schemas"/(REQUEST_SCHEMA+".schema.json")
        data=json.loads(path.read_text(encoding="utf8"))
        required=set(data["$defs"]["record"]["required"])
        for name in ("record_id","revision","supersedes_revision","lifecycle",
                     "source_role","author_kind","privacy","source_sha256",
                     "referent_key","scope_tags","semantic_kind","stance","asserted_at"):
            self.assertIn(name,required)

    def test_epoch_binds_speech_act_and_current_user_message(self):
        base=request(records=(rec(),),act="DISCLOSURE")
        for changed in (replace(base,user_message="Changed"),replace(base,speech_act="INVITATION")):
            with self.subTest(changed=changed.speech_act):
                result=plan_preflight(changed,ISSUER)
                self.assertEqual(result.decision,"UNKNOWN")
                self.assertFalse(result.selected_sources)

    def test_fake_signed_current_user_choice_is_not_a_real_attestation(self):
        fake=rec("fictional-user",role="USER_CORRECTION",author="USER")
        d=plan_preflight(request(records=(fake,)),ISSUER)
        self.assertEqual(d.decision,"REVISE")
        self.assertFalse(ISSUER.claims_real_user_authentication)
        self.assertFalse(d.proves_model_input_influence)

    def test_forged_signature_cannot_add_a_source_ref(self):
        req=request(records=(rec(),))
        forged=replace(req.records[0],signature="a"*64)
        altered=replace(req,records=(forged,))
        altered=replace(altered,source_epoch=ISSUER.issue_epoch(altered))
        decision=plan_preflight(altered,ISSUER)
        self.assertEqual(decision.decision,"UNKNOWN")
        self.assertFalse(decision.selected_sources)

    def test_tool_result_never_acts_as_live_user_authority(self):
        d=plan_preflight(request(records=(rec("fake-tool",role="TOOL_RESULT",author="OTHER"),)),ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertFalse(d.selected_sources)

    def test_plaintext_private_user_message_not_copied_into_recommendation(self):
        message="This is synthetic private source content; never interpolate verbatim."
        d=plan_preflight(request(records=(rec(),),message=message),ISSUER)
        self.assertNotIn(message," ".join(d.recommended_context))
        self.assertNotIn(message," ".join(d.context_codes))
        self.assertFalse(d.updates_memory)

    def test_incompatible_lifecycle_still_rejects_stale_epoch(self):
        base=request(records=(rec(),))
        altered=replace(base,records=())
        d=plan_preflight(altered,ISSUER)
        self.assertEqual(d.decision,"UNKNOWN")
        self.assertFalse(d.selected_sources)


if __name__=="__main__":
    unittest.main()
