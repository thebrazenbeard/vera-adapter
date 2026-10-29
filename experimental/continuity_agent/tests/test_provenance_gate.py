import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from provenance_gate import AdmissionError, evaluate, load_corpus, prepare

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "fixtures" / "synthetic_examples.jsonl"


class ProvenanceGateTests(unittest.TestCase):
    def _load_records(self, records):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "data.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in records) + "\n", encoding="utf-8")
            return load_corpus(path)

    @staticmethod
    def _export(root):
        public = root / "public"
        private = root / "private-key-custody"
        manifest = prepare(SAMPLES, public, private)
        return public, private, manifest

    @staticmethod
    def _predictions(root, public, original=None):
        records = [json.loads(line) for line in
                   (original or ROOT / "fixtures" / "example_predictions.jsonl").read_text().splitlines()]
        subject = hashlib.sha256((public / "manifest.json").read_bytes()).hexdigest()
        predictions = root / "bound_predictions.jsonl"
        predictions.write_text("".join(json.dumps(dict(row, manifest_sha256=subject)) + "\n" for row in records))
        return predictions

    def test_fixture_is_admitted(self):
        self.assertEqual(len(load_corpus(SAMPLES)), 5)

    def test_exports_answer_separated(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            public, private, manifest = self._export(out)
            self.assertEqual(manifest["counts"], {"train": 2, "heldout": 3})
            self.assertNotIn("reference", (public / "holdout_prompts.jsonl").read_text())
            self.assertNotIn('"target"', (public / "holdout_prompts.jsonl").read_text())
            self.assertIn("23 C", (private / "holdout_key.jsonl").read_text())
            self.assertFalse((public / "holdout_key.jsonl").exists())
            self.assertTrue((private / "key_manifest.json").is_file())

    def test_exact_match_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            public, private, _ = self._export(out)
            subject = hashlib.sha256((public / "manifest.json").read_bytes()).hexdigest()
            result = evaluate(public, private, self._predictions(out, public), subject)
            self.assertEqual((result["correct"], result["total"]), (3, 3))

    def test_reject_duplicate_id(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "duplicate ID"):
            self._load_records([r, dict(r, prompt="Different")])

    def test_reject_train_eval_contamination(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "split contamination"):
            self._load_records([r, dict(r, id="other", split="eval", prompt="what IS 3 PLUS 5!!!")])

    def test_reject_model_outputs_as_training_data(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "policy review"):
            self._load_records([dict(r, source_kind="model_output")])

    def test_reject_private_import(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "private/sensitive"):
            self._load_records([dict(r, privacy="private")])

    def test_reject_user_owned_without_consent(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "explicit consent"):
            self._load_records([dict(r, source_kind="user_owned", license="owner_authorized",
                                     source_ref="user-owned:arith-t1", consent="not_required")])

    def test_reject_user_owned_without_external_roster(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "attestation"):
            self._load_records([dict(r, source_kind="user_owned", license="owner_authorized",
                                     source_ref="user-owned:arith-t1", consent="explicit")])

    def test_reject_invalid_license(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "license"):
            self._load_records([dict(r, license="public_domain_maybe")])

    def test_reject_secret_in_metadata(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "PII or secret"):
            self._load_records([dict(r, source_ref="synthetic:operator@example.com")])

    def test_valid_external_roster_binds_exact_record(self):
        from provenance_gate import _record_digest
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        r.update(source_kind="user_owned", license="owner_authorized", source_ref="user-owned:arith-t1", consent="explicit")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data.jsonl"
            data.write_text(json.dumps(r) + "\n")
            roster = root / "attested.json"
            roster.write_text(json.dumps({"schema": "VERA_USER_OWNED_ATTESTATION_V1",
                                          "entries": {r["id"]: _record_digest(r)}}))
            roster_hash = hashlib.sha256(roster.read_bytes()).hexdigest()
            admitted = load_corpus(data, roster, roster_hash)
            self.assertEqual(len(admitted), 1)
            with self.assertRaisesRegex(AdmissionError, "hash mismatch"):
                load_corpus(data, roster, "0" * 64)
            with self.assertRaisesRegex(AdmissionError, "does not match record"):
                data.write_text(json.dumps(dict(r, reference="different")) + "\n")
                load_corpus(data, roster, roster_hash)

    def test_refuse_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "public").mkdir()
            with self.assertRaisesRegex(AdmissionError, "already exists"):
                prepare(SAMPLES, root / "public", root / "key")

    def test_refuse_nested_key_custody(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(AdmissionError, "separate"):
                prepare(SAMPLES, root / "public", root / "public" / "private")

    def test_refuse_symlinked_key_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "link").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(AdmissionError, "symlink"):
                prepare(SAMPLES, root / "public", root / "link" / "private")

    def test_reject_lived_experience_claim(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "lived-experience"):
            self._load_records([dict(r, claim_type="autobiographical_memory")])

    def test_reject_apparent_secret(self):
        r = json.loads(SAMPLES.read_text().splitlines()[0])
        with self.assertRaisesRegex(AdmissionError, "PII or secret"):
            self._load_records([dict(r, prompt="Your api_key=abc123 is what?")])

    def test_no_partial_prediction_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            public, private, _ = self._export(out)
            subject = hashlib.sha256((public / "manifest.json").read_bytes()).hexdigest()
            pred = out / "missing.jsonl"
            pred.write_text(json.dumps({"id": "arith-e1", "response": "11", "manifest_sha256": subject}) + "\n")
            with self.assertRaisesRegex(AdmissionError, "exactly match"):
                evaluate(public, private, pred, subject)

    def test_prediction_subject_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public, private, _ = self._export(root)
            bound = self._predictions(root, public)
            wrong = root / "wrong.jsonl"
            rows = [json.loads(line) for line in bound.read_text().splitlines()]
            rows[0]["manifest_sha256"] = "0" * 64
            wrong.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            subject = hashlib.sha256((public / "manifest.json").read_bytes()).hexdigest()
            with self.assertRaisesRegex(AdmissionError, "subject mismatch"):
                evaluate(public, private, wrong, subject)

    def test_answer_key_integrity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public, private, _ = self._export(root)
            prediction = self._predictions(root, public)
            (private / "holdout_key.jsonl").write_text('{"id":"arith-e1","reference":"tampered"}\n')
            subject = hashlib.sha256((public / "manifest.json").read_bytes()).hexdigest()
            with self.assertRaisesRegex(AdmissionError, "digest mismatch"):
                evaluate(public, private, prediction, subject)

    def test_externally_pinned_subject_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public, private, _ = self._export(root)
            prediction = self._predictions(root, public)
            with self.assertRaisesRegex(AdmissionError, "externally pinned"):
                evaluate(public, private, prediction, "0" * 64)


if __name__ == "__main__":
    unittest.main()
