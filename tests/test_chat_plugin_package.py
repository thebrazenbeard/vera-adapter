"""Source-only Plugin Creator package for explicit ChatGPT text review."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/"plugin"/"vera-midflight-advisory"

class ChatPluginPackageTests(unittest.TestCase):
    def test_manifest_is_optin_not_mandatory_interception(self):
        data=json.loads((PLUGIN/"plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"],"vera-midflight-advisory")
        self.assertEqual(data["version"],"0.1.0")
        ui=data["extensions"]["com.openai"]["interface"]
        self.assertIn("Interactive",ui["capabilities"])
        self.assertIn("Advisory",ui["displayName"])
        self.assertNotIn("automatic",ui["shortDescription"].casefold())

    def test_skill_requires_explicit_optin_and_actual_tool_receipt(self):
        text=(PLUGIN/"skills"/"vera-midflight-advisory"/"SKILL.md").read_text(encoding="utf-8")
        for phrase in ("explicit @mention","actual invocation receipt",
                       "not guaranteed","final-delivery observation",
                       "Do not claim"):
            self.assertIn(phrase,text)

    def test_skill_never_grants_effect_authority(self):
        text=(PLUGIN/"skills"/"vera-midflight-advisory"/"SKILL.md").read_text(encoding="utf-8")
        self.assertIn("never authorizes tools",text)
        self.assertIn("do not install",text)

    def test_reference_exposes_source_only_reproduction(self):
        text=(PLUGIN/"skills"/"vera-midflight-advisory"/"references"/
              "RUNTIME_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("python -B -m unittest discover",text)
        self.assertIn("VERA_CHAT_ADVISORY_V1",text)
        self.assertIn("NO NATIVE INTERCEPTION",text)
