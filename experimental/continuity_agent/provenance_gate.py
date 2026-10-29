"""Prototype provenance-gated behavioral learning/evaluation corpus.

Pure stdlib, no network, model runtime, live-memory writes, or tool effects.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
from pathlib import Path


SPLITS = frozenset({"train", "eval", "challenge"})
SOURCE_KINDS = frozenset({"synthetic", "user_owned", "model_output", "historical_import"})
PRIVACY = frozenset({"public", "private", "sensitive"})
LICENSES = {"synthetic": "original_synthetic", "user_owned": "owner_authorized"}
REQUIRED = frozenset({
    "id", "capability", "prompt", "reference", "split", "source_kind",
    "source_ref", "consent", "privacy", "license", "claim_type",
})
SENSITIVE_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\d)(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)"),
    re.compile(r"\b(?:api[_-]?key|bearer|password|secret)\s*[:=]\s*\S+", re.I),
)


class AdmissionError(ValueError):
    """Untrusted record fails a typed corpus admission condition."""


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold()))


def _fingerprint(item: dict) -> str:
    source = f"{_normalized(item['capability'])}|{_normalized(item['prompt'])}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_digest(item: dict) -> str:
    return _digest(json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def _load_attestations(path: Path | None, expected_sha256: str | None) -> tuple[dict, str | None]:
    if path is None and expected_sha256 is None:
        return {}, None
    if path is None or not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise AdmissionError("external attestation path and trusted lowercase sha256 both required")
    if any(candidate.is_symlink() for candidate in (path.absolute(), *path.absolute().parents)):
        raise AdmissionError("attestation path must not be a symlink")
    content = path.read_bytes()
    if not hmac.compare_digest(_digest(content), expected_sha256):
        raise AdmissionError("attestation roster hash mismatch")
    try:
        roster = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AdmissionError("invalid attestation JSON") from exc
    if not isinstance(roster, dict) or set(roster) != {"schema", "entries"} or roster["schema"] != "VERA_USER_OWNED_ATTESTATION_V1":
        raise AdmissionError("invalid attestation schema")
    entries = roster["entries"]
    if not isinstance(entries, dict) or not all(
        isinstance(k, str) and k and isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
        for k, v in entries.items()
    ):
        raise AdmissionError("invalid attestation entries")
    return entries, expected_sha256


def _admit(item: dict, line_number: int) -> dict:
    if not isinstance(item, dict) or not REQUIRED.issubset(item):
        raise AdmissionError(f"line {line_number}: required fields absent")
    if set(item) != REQUIRED:
        raise AdmissionError(f"line {line_number}: unknown metadata fields")
    if any(not isinstance(item[key], str) or not item[key].strip() for key in REQUIRED):
        raise AdmissionError(f"line {line_number}: fields must be nonblank strings")
    if item["split"] not in SPLITS or item["source_kind"] not in SOURCE_KINDS:
        raise AdmissionError(f"line {line_number}: unknown split/source kind")
    if item["privacy"] not in PRIVACY:
        raise AdmissionError(f"line {line_number}: unknown privacy class")
    if item["privacy"] != "public":
        raise AdmissionError(f"line {line_number}: private/sensitive material is not admitted")
    if item["source_kind"] not in {"synthetic", "user_owned"}:
        raise AdmissionError(f"line {line_number}: model outputs/imports require separate policy review")
    if item["license"] != LICENSES[item["source_kind"]]:
        raise AdmissionError(f"line {line_number}: license token not allowlisted for source kind")
    expected_prefix = "synthetic:" if item["source_kind"] == "synthetic" else "user-owned:"
    if not item["source_ref"].startswith(expected_prefix):
        raise AdmissionError(f"line {line_number}: source reference namespace mismatch")
    if item["source_kind"] == "user_owned" and item["consent"] != "explicit":
        raise AdmissionError(f"line {line_number}: user-owned example lacks explicit consent")
    if item["source_kind"] == "synthetic" and item["consent"] not in {"not_required", "explicit"}:
        raise AdmissionError(f"line {line_number}: synthetic example consent invalid")
    if item["claim_type"] != "task_response":
        raise AdmissionError(f"line {line_number}: no lived-experience or identity claims in learning data")
    # All metadata participates; a poisoned source_ref/ID must not be silently discarded.
    if any(regex.search(json.dumps(item, ensure_ascii=False)) for regex in SENSITIVE_PATTERNS):
        raise AdmissionError(f"line {line_number}: potential PII or secret detected")
    return {key: item[key] for key in sorted(REQUIRED)}


def load_corpus(path: Path, attestations: Path | None = None, attestation_sha256: str | None = None) -> list[dict]:
    entries, _ = _load_attestations(attestations, attestation_sha256)
    admitted = []
    ids = set()
    fingerprints = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdmissionError(f"line {line_number}: invalid JSON") from exc
        item = _admit(data, line_number)
        if item["source_kind"] == "user_owned":
            if not entries:
                raise AdmissionError(f"line {line_number}: user-owned example lacks independently supplied attestation")
            record_hash = _record_digest(item)
            if not hmac.compare_digest(entries.get(item["id"], ""), record_hash):
                raise AdmissionError(f"line {line_number}: user-owned attestation does not match record")
        if item["id"] in ids:
            raise AdmissionError(f"line {line_number}: duplicate ID")
        fingerprint = _fingerprint(item)
        if fingerprint in fingerprints:
            prev = fingerprints[fingerprint]
            raise AdmissionError(
                f"line {line_number}: duplicated normalized prompt/capability "
                f"(previous {prev}); potential split contamination"
            )
        ids.add(item["id"])
        fingerprints[fingerprint] = line_number
        admitted.append(item)
    if not admitted:
        raise AdmissionError("empty admitted corpus")
    return admitted


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.writelines(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def _check_destination(path: Path) -> Path:
    absolute = path.absolute()
    if any(candidate.is_symlink() for candidate in (absolute, *absolute.parents)):
        raise AdmissionError("destination or parent is a symlink")
    if os.path.lexists(absolute):
        raise AdmissionError("destination already exists; refuse overwrite")
    return absolute


def prepare(corpus_path: Path, public_directory: Path, key_directory: Path,
            attestations: Path | None = None, attestation_sha256: str | None = None) -> dict:
    """Export student-facing data and separately held evaluation key."""
    # The public API admits from original bytes; callers cannot bypass admission
    # by invoking prepare() with a hand-crafted list of unreviewed records.
    corpus = load_corpus(corpus_path, attestations, attestation_sha256)
    public = _check_destination(public_directory)
    private = _check_destination(key_directory)
    if public == private or public in private.parents or private in public.parents:
        raise AdmissionError("answer-key custody path must be separate, not nested")
    train = [{"id": r["id"], "prompt": r["prompt"], "target": r["reference"],
              "capability": r["capability"], "source_kind": r["source_kind"],
              "source_ref": r["source_ref"], "license": r["license"]}
             for r in corpus if r["split"] == "train"]
    holdout = [{"id": r["id"], "prompt": r["prompt"], "capability": r["capability"],
                "split": r["split"]}
               for r in corpus if r["split"] != "train"]
    answers = [{"id": r["id"], "reference": r["reference"],
                "capability": r["capability"], "split": r["split"]}
               for r in corpus if r["split"] != "train"]
    public.mkdir(parents=True, exist_ok=False)
    private.mkdir(parents=True, exist_ok=False)
    write_jsonl(public / "train.jsonl", train)
    write_jsonl(public / "holdout_prompts.jsonl", holdout)
    write_jsonl(private / "holdout_key.jsonl", answers)
    manifest = {
        "schema": "VERA_BEHAVIORAL_CORPUS_PROTOTYPE_V1",
        "source_scope": "explicit synthetic or consented user-owned examples",
        "artifact_class": "DATASET_EXPORT_NOT_TRAINING_OR_IDENTITY_PROOF",
        "attestation_roster_sha256": attestation_sha256,
        "counts": {"train": len(train), "heldout": len(holdout)},
        "sha256": {filename: _digest((public / filename).read_bytes())
                   for filename in ("train.jsonl", "holdout_prompts.jsonl")},
    }
    (public / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (private / "key_manifest.json").write_text(json.dumps({
        "schema": "VERA_PRIVATE_ANSWER_KEY_MANIFEST_V1",
        "public_manifest_sha256": _digest((public / "manifest.json").read_bytes()),
        "holdout_key_sha256": _digest((private / "holdout_key.jsonl").read_bytes()),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def evaluate(public_directory: Path, key_directory: Path, predictions_path: Path,
             expected_manifest_sha256: str) -> dict:
    """Score manifest-bound predictions against separately custodied key."""
    manifest_bytes = (public_directory / "manifest.json").read_bytes()
    manifest_hash = _digest(manifest_bytes)
    if not isinstance(expected_manifest_sha256, str) or not hmac.compare_digest(manifest_hash, expected_manifest_sha256):
        raise AdmissionError("externally pinned manifest subject mismatch")
    manifest = json.loads(manifest_bytes)
    key_manifest = json.loads((key_directory / "key_manifest.json").read_text(encoding="utf-8"))
    if key_manifest.get("public_manifest_sha256") != manifest_hash:
        raise AdmissionError("public/key manifest subject mismatch")
    if key_manifest.get("schema") != "VERA_PRIVATE_ANSWER_KEY_MANIFEST_V1":
        raise AdmissionError("invalid answer key manifest schema")
    for name in ("train.jsonl", "holdout_prompts.jsonl"):
        if _digest((public_directory / name).read_bytes()) != manifest.get("sha256", {}).get(name):
            raise AdmissionError("public corpus digest mismatch")
    key_path = key_directory / "holdout_key.jsonl"
    if _digest(key_path.read_bytes()) != key_manifest.get("holdout_key_sha256"):
        raise AdmissionError("answer key digest mismatch")
    keys = [json.loads(line) for line in key_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompts = [json.loads(line) for line in (public_directory / "holdout_prompts.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(keys) != manifest["counts"]["heldout"] or len(prompts) != len(keys) or {
        r["id"] for r in keys
    } != {r["id"] for r in prompts}:
        raise AdmissionError("answer key/holdout ID mismatch")
    preds = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {}
    for p in preds:
        if not isinstance(p, dict) or set(p) != {"id", "response", "manifest_sha256"} or not isinstance(p.get("id"), str) or not isinstance(p.get("response"), str):
            raise AdmissionError("prediction must contain string id, response and manifest_sha256")
        if p["manifest_sha256"] != manifest_hash:
            raise AdmissionError("prediction manifest subject mismatch")
        if p["id"] in by_id:
            raise AdmissionError("duplicate prediction ID")
        by_id[p["id"]] = p["response"]
    expected_ids = {r["id"] for r in keys}
    if set(by_id) != expected_ids:
        raise AdmissionError("prediction IDs must exactly match held-out key")
    counts = {}
    for r in keys:
        bucket = counts.setdefault(r["capability"], {"correct": 0, "total": 0})
        bucket["total"] += 1
        bucket["correct"] += int(_normalized(by_id[r["id"]]) == _normalized(r["reference"]))
    return {"method": "normalized_exact_match", "public_manifest_sha256": manifest_hash, "counts": counts,
            "total": sum(v["total"] for v in counts.values()),
            "correct": sum(v["correct"] for v in counts.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("corpus", type=Path)
    prep.add_argument("public_dir", type=Path)
    prep.add_argument("key_dir", type=Path)
    prep.add_argument("--attestations", type=Path)
    prep.add_argument("--attestation-sha256", type=str)
    eval_p = commands.add_parser("evaluate")
    eval_p.add_argument("public_dir", type=Path)
    eval_p.add_argument("key_dir", type=Path)
    eval_p.add_argument("predictions", type=Path)
    eval_p.add_argument("--subject-sha256", required=True)
    args = parser.parse_args()
    result = (prepare(args.corpus, args.public_dir, args.key_dir, args.attestations, args.attestation_sha256)
              if args.command == "prepare" else evaluate(args.public_dir, args.key_dir,
                                                          args.predictions, args.subject_sha256))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
