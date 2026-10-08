import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vera_adapter.attempt import attempt_claim_path, claim_attempt
from vera_adapter.core import AdapterRequest
from vera_adapter.drift import EngineTarget
from vera_adapter.identity import IdentityCapsule, SourceRef
from vera_adapter.ir import VeraIR


class Driver:
    provider = "local"
    model = "stub-model"

    def complete(self, envelope):
        raise AssertionError("claim validation must not call an engine")


def req(sources=None):
    if sources is None:
        sources = (SourceRef("repo", "a" * 40, "identity.json"),)
    return AdapterRequest("t1", VeraIR(
        IdentityCapsule({"name": "Vera"}, (), sources=sources),
        conversation=("test",),
    ))


def targets():
    return (EngineTarget("one", "stub", Driver(), "declared-not-verified"),)


class AttemptClaimTests(unittest.TestCase):
    def test_claim_created_before_dispatch_is_bound_and_exclusive(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "evidence.json"
            first = claim_attempt(dest, req(), targets(),
                                  source_revision="a" * 40,
                                  target_manifest_sha256="f" * 64)
            payload = json.loads(attempt_claim_path(dest).read_text())
            self.assertEqual(payload["claim_sha256"], first)
            self.assertEqual(payload["retry_policy"], "NO_AUTOMATIC_RETRY")
            self.assertEqual(payload["status"],
                             "CLAIMED_BEFORE_DISPATCH_NOT_PROOF_OF_ENGINE_EXECUTION")
            self.assertFalse(dest.exists())
            with self.assertRaises(FileExistsError):
                claim_attempt(dest, req(), targets(), source_revision="a" * 40,
                              target_manifest_sha256="f" * 64)

    def test_fails_before_attempt_if_provenance_missing(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            with self.assertRaises(ValueError):
                claim_attempt(dest, req(sources=()), targets(),
                              source_revision="a" * 40,
                              target_manifest_sha256=None)
            self.assertFalse(attempt_claim_path(dest).exists())

    def test_fails_before_attempt_if_second_target_invalid(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            invalid = targets() + (EngineTarget("two", "", Driver()),)
            with self.assertRaises(ValueError):
                claim_attempt(dest, req(), invalid, source_revision="a" * 40,
                              target_manifest_sha256=None)
            self.assertFalse(attempt_claim_path(dest).exists())

    def test_interrupted_claim_write_is_not_silently_cleared(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "evidence.json"
            path = attempt_claim_path(dest)
            path.write_bytes(b'{"incomplete":')
            with self.assertRaises(FileExistsError):
                claim_attempt(dest, req(), targets(), source_revision="a" * 40,
                              target_manifest_sha256=None)
            self.assertEqual(path.read_bytes(), b'{"incomplete":')

    def test_claim_no_overwrite_when_output_exists(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "evidence.json"
            dest.write_text("protected original")
            with self.assertRaises(FileExistsError):
                claim_attempt(dest, req(), targets(), source_revision="a" * 40,
                              target_manifest_sha256=None)
            self.assertFalse(attempt_claim_path(dest).exists())
            self.assertEqual(dest.read_text(), "protected original")


if __name__ == "__main__":
    unittest.main()
