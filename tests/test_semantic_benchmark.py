"""Reproducibility, no exact-text reuse, controlled negative examples."""
from hashlib import sha256
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
BENCH=ROOT/"benchmarks"/"semantic_correction"
SOURCE=ROOT/"vera_adapter"/"semantic_correction.py"


def read_json(name):
    return json.loads((BENCH/name).read_text())


def corpus(name):
    return [json.loads(x) for x in (BENCH/name).read_text().splitlines()]


class SourceBoundBenchmarkTests(unittest.TestCase):
    def test_h3_source_and_corpus_seals(self):
        m=read_json("corpus_manifest_v3.json")
        self.assertEqual(m["schema"],"VERA_SYNTHETIC_CORRECTION_CORPUS_V3")
        self.assertEqual(sha256(SOURCE.read_bytes()).hexdigest(),
                         m["candidate_source_sha256"])
        split=m["splits"]["HOLDOUT_V3"]
        self.assertEqual(sha256((BENCH/split["path"]).read_bytes()).hexdigest(),
                         split["sha256"])
        cases=corpus(split["path"])
        self.assertEqual(len(cases),270)
        self.assertEqual(sum(x["gold"]=="NEEDS_REVISION" for x in cases),108)
        self.assertEqual(sum(x["gold"]=="ACCEPTABLE" for x in cases),144)
        self.assertEqual(sum(x["gold"]=="ABSTAIN" for x in cases),18)

    def test_h3_has_no_exact_response_overlap_or_duplicate_ids(self):
        earlier=set()
        for name in ("design.jsonl","holdout.jsonl","holdout_v2.jsonl"):
            earlier.update(c["text"] for c in corpus(name))
        latest=corpus("holdout_v3.jsonl")
        texts=[c["text"] for c in latest]
        self.assertEqual(len(texts),len(set(texts)))
        self.assertFalse(set(texts)&earlier)
        self.assertEqual(len(latest),len({x["id"] for x in latest}))

    def test_pilot_reuse_disclosed_instead_of_laundered(self):
        d=set(x["text"] for x in corpus("design.jsonl"))
        h=set(x["text"] for x in corpus("holdout.jsonl"))
        self.assertEqual(len(d & h),69)
        self.assertEqual(read_json("corpus_manifest_v3.json")["warning"].startswith(
            "Single-author"),True)

    def test_fixed_h3_report_is_paired_and_anti_overcorrection(self):
        a=read_json("holdout_v3_baseline_report.json")
        b=read_json("holdout_v3_candidate_report.json")
        c=read_json("holdout_v3_negative_control_report.json")
        self.assertEqual({a["holdout_sha256"],b["holdout_sha256"],c["holdout_sha256"]},
                         {read_json("corpus_manifest_v3.json")["splits"]["HOLDOUT_V3"]["sha256"]})
        self.assertEqual(a["confusion"]["tp"],0)
        self.assertEqual(b["confusion"]["tp"],90)
        self.assertEqual(b["confusion"]["fp"],0)
        self.assertEqual(b["confusion"]["fn"],18)
        self.assertEqual(b["confusion"]["required_abstention_correct"],18)
        self.assertEqual(c["confusion"]["tp"],0)
        self.assertEqual(b["metrics"]["unchanged_good_rate"],1.0)
        self.assertFalse(b["limitations"]["heldout_independent_operator"])

    def test_pinned_driftguard_policy_passes_h3_not_controls(self):
        good=read_json("holdout_v3_candidate_driftguard_gate.json")
        bad=read_json("holdout_v3_negative_control_driftguard_gate.json")
        self.assertEqual(good["schema"],"DRIFTGUARD_CI_GATE_RESULT_V1")
        self.assertEqual(good["decision"],"PASS")
        self.assertEqual(bad["decision"],"BLOCK")
        self.assertEqual(good["policy_digest"],bad["policy_digest"])
        self.assertEqual(good["policy_digest"],
            "871595faf5c9f2779744cbe1f2601d6ea9400359d3a838f3f855efb0116a901c")
        blocked=read_json("holdout_v2_candidate_driftguard_gate.json")
        self.assertEqual(blocked["decision"],"BLOCK")


if __name__=="__main__":
    unittest.main()
