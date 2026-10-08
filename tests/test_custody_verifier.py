import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_adapter.attempt import attempt_claim_path, claim_attempt
from vera_adapter.core import AdapterRequest
from vera_adapter.custody import EvidenceHold, verify_local_evidence
from vera_adapter.drift import EngineTarget, digest, run_unrescued, write_exclusive
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.ir import VeraIR


class Stub:
    provider = "mock"
    model = "mock-model"

    def complete(self, envelope):
        return "Observed text that is not independent qualification"


def request():
    return AdapterRequest(
        "frozen-001",
        VeraIR(IdentityCapsule(
            {"name": "Vera"}, ("Preserve evidence scope",),
            sources=(SourceRef("repo", "a" * 40, "identity.json"),),
        ), conversation=("Provide evidence distinctions",)),
    )


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "result.json"
        self.req = request()
        self.targets = (EngineTarget("engine-A", "mock", Stub(), "unverified-A"),)

    def claim(self):
        return claim_attempt(
            self.output, self.req, self.targets,
            source_revision="a" * 40, target_manifest_sha256="e" * 64,
        )

    def complete(self):
        sha = self.claim()
        obs = run_unrescued(
            self.req, self.targets, source_revision="a" * 40,
            target_manifest_sha256="e" * 64, attempt_claim_sha256=sha,
        )
        write_exclusive(self.output, obs)

    def test_exact_claim_receipt_pair_passes_internal_custody(self):
        self.complete()
        result = verify_local_evidence(self.output)
        self.assertEqual(result.status, "PASS_INTERNAL_CUSTODY_ONLY")
        self.assertEqual(result.observation_count, 1)

    def test_claim_without_result_is_held_ambiguous(self):
        self.claim()
        with self.assertRaisesRegex(EvidenceHold, "HOLD_CLAIMED_NO_RESULT"):
            verify_local_evidence(self.output)

    def test_corrupted_result_checksum_rejected(self):
        self.complete()
        payload = json.loads(self.output.read_text())
        payload["observations"][0]["text"] = "unexpected replacement"
        self.output.write_text(json.dumps(payload))
        with self.assertRaisesRegex(EvidenceHold, "SHA-256 mismatch"):
            verify_local_evidence(self.output)

    def test_rehashed_result_cannot_change_target_binding(self):
        self.complete()
        payload = json.loads(self.output.read_text())
        payload["observations"][0]["model"] = "imposter-model"
        payload.pop("receipt_sha256")
        payload["receipt_sha256"] = digest(payload)
        self.output.write_text(json.dumps(payload))
        with self.assertRaisesRegex(EvidenceHold, "changed target model"):
            verify_local_evidence(self.output)

    def test_rehashed_claim_changes_subject_and_fails_link(self):
        self.complete()
        claim_path = attempt_claim_path(self.output)
        claim = json.loads(claim_path.read_text())
        claim["targets"][0]["model"] = "forged-model"
        claim.pop("claim_sha256")
        claim["claim_sha256"] = digest(claim)
        claim_path.write_text(json.dumps(claim))
        with self.assertRaisesRegex(EvidenceHold, "claim digest mismatch"):
            verify_local_evidence(self.output)

    def test_both_files_missing_does_not_pass(self):
        with self.assertRaisesRegex(EvidenceHold, "claim: missing"):
            verify_local_evidence(self.output)


if __name__ == "__main__":
    unittest.main()
