"""Run a pinned, synthetic cross-repository model-neutral contract check.

Usage:
    python3 -I -S -B scripts/verify_model_neutral_interop.py \
      --sources-root /path/to/checked-out-sources \
      --conations-head SHA --empathy-head SHA --pleasure-head SHA \
      --volition-head SHA --meso-crct-head SHA

The source directories must be clean, exact Git checkouts, without import-root
symlinks or cached bytecode. The isolated, no-site Python interpreter prevents
site and environment path injection. The source modules are still executable
code; only use source trees whose provenance you have independently checked.
This is source-only custody, not host, model, provider, or permission attestation.
"""

from __future__ import annotations

import argparse
import importlib
from importlib.machinery import (
    BuiltinImporter, FrozenImporter, PathFinder, SourceFileLoader,
)
from importlib.machinery import ModuleSpec
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import FunctionType, ModuleType
import unittest


HEAD = re.compile(r"[0-9a-f]{40}\Z")
_MODULES: dict[str, object] = {}
_IMPORT_OWNERS = {
    "conation_history_context": "conations",
    "conation_manifest": "conations",
    "empathy_research": "empathy",
    "pleasure_experiment": "pleasure",
    "meso_crct": "meso-crct",
    "volition": "volition",
}


def _module_owner(name: str) -> str | None:
    for prefix, owner in _IMPORT_OWNERS.items():
        if name == prefix or name.startswith(prefix + "."):
            return owner
    return None


def _reject_preloaded_imports() -> None:
    # sys.path precedence cannot override an already cached module object.
    preloaded = sorted(name for name in sys.modules if _module_owner(name))
    if preloaded:
        raise ValueError("preloaded checked-source module is not admissible")


def _checked_file(path: Path, root: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("module origin is not an absolute canonical file path")
    try:
        anchor = root.resolve(strict=True)
        canonical = path.resolve(strict=True)
        canonical.relative_to(anchor)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("module source escapes pinned import root") from exc
    if not canonical.is_file() or path.suffix != ".py":
        raise ValueError("module origin is not a regular Python source file")
    current = path
    while current != anchor:
        if current.is_symlink():
            raise ValueError("symlinked module source is not admissible")
        current = current.parent
        if current == current.parent and current != anchor:
            raise ValueError("module path is outside pinned import root")
    return canonical


def _preflight_import_root(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("pinned import root is missing or symlinked")
    # Include ignored files. Git's clean status alone misses ignored pyc files
    # and source-shadowing symlinks that Python could import.
    for current, directories, files in os.walk(root, followlinks=False):
        for entry in directories + files:
            candidate = Path(current) / entry
            if candidate.is_symlink():
                raise ValueError("symlink in pinned import root")
            if candidate.suffix == ".pyc" or entry == "__pycache__":
                raise ValueError("cached bytecode in pinned import root")


def _validate_module_origin(name: str, module: object, root: Path) -> None:
    """Require a file-backed real import, not a forged __file__ claim alone."""
    if type(module) is not ModuleType:
        raise ValueError("imported checked-source object is not a module")
    spec = getattr(module, "__spec__", None)
    if not isinstance(spec, ModuleSpec) or spec.name != name:
        raise ValueError("missing or conflicting module spec")
    if type(spec.loader) is not SourceFileLoader or module.__loader__ is not spec.loader:
        raise ValueError("module did not use a source-file loader")
    origins = (
        getattr(module, "__file__", None),
        spec.origin,
        getattr(spec.loader, "path", None),
        spec.loader.get_filename(name),
    )
    if any(type(value) is not str for value in origins):
        raise ValueError("non-file module origin")
    canonical = _checked_file(Path(origins[0]), root)
    if any(_checked_file(Path(value), root) != canonical for value in origins[1:]):
        raise ValueError("conflicting loaded module origins")


def _verify_bound_function(value: object, owner_root: Path) -> None:
    if type(value) is not FunctionType:
        raise ValueError("checked source export is not a Python function")
    _checked_file(Path(value.__code__.co_filename), owner_root)


def _verify_loaded_imports(roots: dict[str, Path]) -> None:
    for name, module in tuple(sys.modules.items()):
        owner = _module_owner(name)
        if owner is not None:
            _validate_module_origin(name, module, roots[owner])
    # Check the code object's actual compiled filename as well as the
    # module metadata; a forged __file__ alone cannot pass this check.
    for name, source in (
        ("parse_history_export", "conations"),
        ("response_policy_hint", "empathy"),
        ("with_historical_conations", "empathy"),
        ("derive_action_tendency", "meso-crct"),
        ("propose_action_intent", "meso-crct"),
        ("select_target", "meso-crct"),
    ):
        _verify_bound_function(_MODULES[name], roots[source])
    for method, source in (
        (_MODULES["ExperimentalPleasureRuntime"].step, "pleasure"),
        (_MODULES["MesoIntentBridge"].to_signals, "volition"),
    ):
        _verify_bound_function(method, roots[source])


def _require_isolated_interpreter() -> None:
    if not sys.flags.isolated or not sys.flags.no_site:
        raise ValueError("source custody requires python -I -S -B")
    if not sys.flags.dont_write_bytecode or not sys.dont_write_bytecode:
        raise ValueError("source custody requires -B: bytecode writes must be disabled")
    if tuple(sys.meta_path) != (BuiltinImporter, FrozenImporter, PathFinder):
        raise ValueError("nonstandard import hook in source-custody interpreter")


def _pin_source(root: Path, name: str, expected: str) -> Path:
    if not HEAD.fullmatch(expected):
        raise ValueError(f"{name}: expected head must be a full lowercase Git SHA")
    path = root / name
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{name}: missing or symlinked source directory")
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--verify", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    if completed.stdout.strip() != expected:
        raise ValueError(f"{name}: source HEAD is not the requested identity")
    status = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    if status.stdout:
        raise ValueError(f"{name}: source worktree is not clean")
    return path


def _bind_modules(source_root: Path, heads: dict[str, str]) -> None:
    _reject_preloaded_imports()
    roots: dict[str, Path] = {}
    for name, head in heads.items():
        path = _pin_source(source_root, name, head)
        root = path / "src" if name in ("volition", "meso-crct") else path
        _preflight_import_root(root)
        roots[name] = root
        sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    from conation_history_context import HistoryContextError, parse_history_export
    from empathy_research.integration_contract import (
        response_policy_hint, with_historical_conations,
    )
    from empathy_research.policy import Assessment, Evidence
    from pleasure_experiment.runtime import (
        ExperimentalPleasureRuntime, Observation, PilotConfig,
    )
    from meso_crct import (
        CircuitState, SalienceState, TargetState,
        derive_action_tendency, propose_action_intent, select_target,
    )
    from volition.meso_bridge import MesoIntentBridge
    from volition.models import DriveKind, ProvenanceClass
    _MODULES.update(locals())
    _verify_loaded_imports(roots)


def _manifest() -> dict[str, object]:
    return {
        "schema": "conations.history.v1",
        "currentness": "history_only",
        "effect_authority": "none",
        "activation": "fresh_reappraisal_required",
        "events": [{
            "event_date": "2026-01-02", "event_type": "ADD",
            "content_sha256": "a" * 64, "status_currentness": "historical_only",
            "path": "events/2026-01-02/synthetic.md",
            "subject": "SYNTHETIC_ONLY", "recorded_status": "REVOKED",
        }],
    }


class CrossRepositoryContracts(unittest.TestCase):
    def test_history_is_inert_and_scrubbed(self) -> None:
        parse = _MODULES["parse_history_export"]
        history = parse(json.dumps(_manifest()))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].evidence_class, "HISTORICAL_ONLY")
        self.assertFalse(hasattr(history[0], "subject"))
        self.assertFalse(hasattr(history[0], "path"))

        assessment = _MODULES["Assessment"](person_id="synthetic-person-A")
        attached = _MODULES["with_historical_conations"](assessment, history)
        hint = _MODULES["response_policy_hint"](attached)
        self.assertNotEqual(hint.policy, "TASK_DIRECT")
        self.assertEqual(hint.authority, "NONE")
        self.assertFalse(hint.effect_authority)
        self.assertFalse(hint.volition_want_authority)
        self.assertFalse(attached.historical_evidence[0].active)
        self.assertEqual(attached.historical_evidence[0].source, "historical")
        self.assertEqual(attached.historical_evidence[0].scope_person_id, "synthetic-person-A")

    def test_history_does_not_change_current_task_route(self) -> None:
        Evidence, Assessment = _MODULES["Evidence"], _MODULES["Assessment"]
        assessment = Assessment(person_id="synthetic-person-A", current_evidence=(
            Evidence(
                kind="task_request", referent="task", value="act",
                confidence=0.95, source="current",
                scope_person_id="synthetic-person-A",
                evidence_id="ev_" + "b" * 32,
            ),
        ))
        before = _MODULES["response_policy_hint"](assessment)
        history = _MODULES["parse_history_export"](json.dumps(_manifest()))
        after = _MODULES["response_policy_hint"](
            _MODULES["with_historical_conations"](assessment, history)
        )
        self.assertEqual(before, after)
        self.assertEqual(after.policy, "TASK_DIRECT")
        self.assertFalse(after.effect_authority)

    def test_currentness_consent_and_duplicate_keys_denied(self) -> None:
        parse, error = _MODULES["parse_history_export"], _MODULES["HistoryContextError"]
        for mutation in ("currentness", "consent"):
            record = _manifest()
            if mutation == "currentness":
                record["events"][0]["status_currentness"] = "current"
            else:
                record["events"][0]["consent"] = "ALLOW"
            with self.subTest(mutation=mutation), self.assertRaises(error):
                parse(json.dumps(record))
        raw = json.dumps(_manifest()).replace(
            '"currentness": "history_only",',
            '"currentness": "history_only", "currentness": "current",',
        )
        with self.assertRaises(error):
            parse(raw)

    def test_two_models_do_not_share_state_or_evidence(self) -> None:
        Config = _MODULES["PilotConfig"]
        Engine = _MODULES["ExperimentalPleasureRuntime"]
        Observation = _MODULES["Observation"]

        def make_engine(model: str, subject: str):
            return Engine(Config(
                model_id=model, model_revision="synthetic-r1",
                runtime_instance_id="synthetic-run-" + subject,
                subject_id=subject, evaluator_id="synthetic-evaluator",
                measurement_definition_id="synthetic-rule",
            ))

        a = make_engine("synthetic-model-A", "synthetic-subject-A")
        b = make_engine("synthetic-model-B", "synthetic-subject-B")
        outcome = Observation(
            subject_id="synthetic-subject-A",
            evaluator_id="synthetic-evaluator",
            evidence_id="synthetic-evidence-1",
            context_id="synthetic-context", reward=0.8,
        )
        receipt = a.step(outcome, elapsed_ms=1000)
        self.assertEqual(receipt.model_id, "synthetic-model-A")
        self.assertEqual(a.state.sequence, 1)
        self.assertEqual(b.state.sequence, 0)
        with self.assertRaises(ValueError):
            b.step(outcome, elapsed_ms=1000)
        with self.assertRaises(ValueError):
            a.step(outcome, elapsed_ms=1000)
        self.assertEqual(b.state.sequence, 0)
        self.assertEqual(a.state.sequence, 1)

    def test_meso_proposal_to_volition_is_non_executable_evidence(self) -> None:
        state = _MODULES["CircuitState"](
            salience=_MODULES["SalienceState"](incentive_salience=0.9),
        )
        tendency = _MODULES["derive_action_tendency"](
            _MODULES["select_target"](
                [_MODULES["TargetState"]("synthetic-target", state)]
            )
        )
        intent = _MODULES["propose_action_intent"](tendency)
        self.assertFalse(intent.effect_authorized)
        self.assertFalse(intent.can_execute)
        signals = _MODULES["MesoIntentBridge"].to_signals(intent)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].target, "synthetic-target")
        self.assertEqual(signals[0].kind, _MODULES["DriveKind"].OPEN_LOOP)
        self.assertEqual(signals[0].provenance, _MODULES["ProvenanceClass"].MODEL_GENERATED)

    def test_meso_forged_execution_claim_denied_by_volition(self) -> None:
        forged = {
            "target_id": "synthetic-target", "kind": "approach",
            "strength": 0.9, "source_tendency": "approach",
            "source": "synthetic", "effect_authorized": True,
            "can_execute": True,
        }
        with self.assertRaises(ValueError):
            _MODULES["MesoIntentBridge"].to_signals(forged)
        forged["effect_authorized"] = False
        with self.assertRaises(ValueError):
            _MODULES["MesoIntentBridge"].to_signals(forged)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-root", type=Path, required=True)
    for name in ("conations", "empathy", "pleasure", "volition", "meso-crct"):
        parser.add_argument(f"--{name}-head", required=True)
    args = parser.parse_args()
    heads = {name: getattr(args, f"{name}_head") for name in (
        "conations", "empathy", "pleasure", "volition"
    )}
    heads["meso-crct"] = args.meso_crct_head
    try:
        _require_isolated_interpreter()
        _bind_modules(args.sources_root.resolve(), heads)
    except (OSError, ValueError, subprocess.CalledProcessError, ImportError) as exc:
        print(f"SOURCE_PRECHECK_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CrossRepositoryContracts)
    )
    print(json.dumps({
        "evidence_class": "SOURCE_TEST_ONLY",
        "source_heads": heads,
        "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "installed_runtime_qualified": False,
        "host_authority_qualified": False,
        "source_import_origin_checked": True,
    }, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
