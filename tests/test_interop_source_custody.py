"""Adversarial source-provenance checks for the offline interop runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
import unittest
from unittest.mock import patch


RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "verify_model_neutral_interop.py"
spec = importlib.util.spec_from_file_location("interop_source_custody_under_test", RUNNER)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def _fake_import_cache() -> dict[str, ModuleType]:
    exports = {
        "conation_history_context": ("HistoryContextError", "parse_history_export"),
        "empathy_research": (),
        "empathy_research.integration_contract": (
            "response_policy_hint", "with_historical_conations",
        ),
        "empathy_research.policy": ("Assessment", "Evidence"),
        "pleasure_experiment": (),
        "pleasure_experiment.runtime": (
            "ExperimentalPleasureRuntime", "Observation", "PilotConfig",
        ),
        "meso_crct": (
            "CircuitState", "SalienceState", "TargetState",
            "derive_action_tendency", "propose_action_intent", "select_target",
        ),
        "volition": (),
        "volition.meso_bridge": ("MesoIntentBridge",),
        "volition.models": ("DriveKind", "ProvenanceClass"),
    }
    modules = {}
    for name, fields in exports.items():
        fake = ModuleType(name)
        fake.__file__ = "/synthetic/pinned-looking/path.py"
        if name in ("empathy_research", "pleasure_experiment", "volition"):
            fake.__path__ = []
        for field in fields:
            setattr(fake, field, object())
        modules[name] = fake
    return modules


class ImportCustodyTests(unittest.TestCase):
    def test_isolated_guard_requires_no_bytecode_flag(self) -> None:
        # Execute only the guard in a fresh interpreter. Never import the
        # five pinned external source trees while -B is absent.
        probe = (
            "import runpy, sys\n"
            "ns = runpy.run_path(sys.argv[1], run_name='interop_guard_probe')\n"
            "try:\n"
            "    ns['_require_isolated_interpreter']()\n"
            "except ValueError as exc:\n"
            "    print(str(exc))\n"
            "    raise SystemExit(2)\n"
        )
        for flags, expected_exit in (
            (("-I", "-S"), 2),
            (("-I", "-S", "-B"), 0),
        ):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    [sys.executable, *flags, "-c", probe, str(RUNNER)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, expected_exit, result.stderr)
                if expected_exit == 2:
                    self.assertIn("bytecode", result.stdout.lower())

    def test_preloaded_fake_modules_must_not_bypass_pins(self) -> None:
        # RED on the original runner: all the from-imports resolve directly
        # from sys.modules, so _bind_modules reports success despite fake code.
        with patch.dict(sys.modules, _fake_import_cache()):
            with patch.object(runner, "_pin_source", return_value=Path("/synthetic/pin")):
                with patch.object(sys, "path", list(sys.path)):
                    with self.assertRaisesRegex(ValueError, "preloaded"):
                        runner._bind_modules(
                            Path("/synthetic"), {
                                "conations": "0" * 40,
                                "empathy": "0" * 40,
                                "pleasure": "0" * 40,
                                "volition": "0" * 40,
                                "meso-crct": "0" * 40,
                            },
                        )

    def test_nonfile_module_and_conflicting_origin_must_fail(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder)
            actual = root / "expected.py"
            actual.write_text("VALUE = 1\n", encoding="utf-8")
            fake = ModuleType("example")
            fake.__file__ = str(actual)
            with self.assertRaises(ValueError):
                runner._validate_module_origin("example", fake, root)
            fake.__spec__ = importlib.util.spec_from_file_location(
                "example", root / "other.py"
            )
            with self.assertRaises(ValueError):
                runner._validate_module_origin("example", fake, root)

    def test_symlink_escape_must_fail_even_with_matching_origin_fields(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder) / "pinned"
            root.mkdir()
            outside = Path(folder) / "outside.py"
            outside.write_text("VALUE = 7\n", encoding="utf-8")
            link = root / "claimed.py"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable in this environment")
            fake = ModuleType("claimed")
            fake.__file__ = str(link)
            fake.__spec__ = importlib.util.spec_from_file_location("claimed", link)
            fake.__loader__ = fake.__spec__.loader
            with self.assertRaises(ValueError):
                runner._validate_module_origin("claimed", fake, root)

    def test_preimport_symlink_source_escape_rejected(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder) / "pinned"
            root.mkdir()
            outside = Path(folder) / "outside.py"
            outside.write_text("VALUE = 7\n", encoding="utf-8")
            try:
                (root / "shadow.py").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable in this environment")
            with self.assertRaisesRegex(ValueError, "symlink"):
                runner._preflight_import_root(root)

    def test_ignored_cached_bytecode_rejected_before_import(self) -> None:
        with TemporaryDirectory() as folder:
            root = Path(folder) / "pinned"
            cache = root / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "shadow.cpython-312.pyc").write_bytes(b"ignored-untrusted-bytecode")
            with self.assertRaisesRegex(ValueError, "bytecode"):
                runner._preflight_import_root(root)


if __name__ == "__main__":
    unittest.main()
