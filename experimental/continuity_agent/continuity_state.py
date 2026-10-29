"""Pure candidate continuity-change ledger, with no persistence or runtime binding.

This module never writes data and cannot grant tool/action authority.
"""

from __future__ import annotations

from copy import deepcopy


class ContinuityError(ValueError):
    pass


# Deliberately small set: all other durable state-change classes require review.
ADMITTED = {
    "user_preference": ("CONFIGURABLE_STATE", "explicit_user_instruction", "user_owned", "preference:"),
    "historical_evidence_import": ("MEMORY_STATE", "explicit_user_import", "historical_import", "historical_evidence:"),
    "evaluated_skill_candidate": ("PLASTIC_STATE", "heldout_evaluation", "training_artifact", "skill_candidate:"),
}


def apply_candidate_change(snapshot: dict, change: dict) -> dict:
    """Append a typed candidate, fail on stale version or unsupported write class.

    This is a proposal store only; accepted skill, memory or identity changes need
    a separate admitted lifecycle in the real runtime.
    """
    if not isinstance(snapshot, dict) or not isinstance(change, dict):
        raise ContinuityError("snapshot/change must be mappings")
    if set(snapshot) != {"version", "changes"} or not isinstance(snapshot["version"], int):
        raise ContinuityError("invalid snapshot")
    if snapshot["version"] < 0 or not isinstance(snapshot["changes"], list):
        raise ContinuityError("invalid snapshot version/changes")
    change_class = change.get("change_class")
    expected = ADMITTED.get(change_class)
    if expected is None:
        raise ContinuityError("state-change class requires separate authority/review")
    family, authority, origin, namespace = expected
    for key, value in (("state_family", family), ("authority", authority), ("origin", origin)):
        if change.get(key) != value:
            raise ContinuityError(f"wrong {key} for {change_class}")
    if change.get("prior_version") != snapshot["version"]:
        raise ContinuityError("stale prior_version")
    if change.get("successor_version") != snapshot["version"] + 1:
        raise ContinuityError("noncontiguous successor_version")
    for field in ("change_id", "target", "trigger", "timestamp", "evidence_refs"):
        if field not in change or not change[field]:
            raise ContinuityError(f"missing {field}")
    if not isinstance(change["target"], str) or not change["target"].startswith(namespace) or len(change["target"]) == len(namespace):
        raise ContinuityError("target is outside class-scoped namespace")
    if not isinstance(change["evidence_refs"], list) or not all(isinstance(r, str) and r for r in change["evidence_refs"]):
        raise ContinuityError("invalid evidence_refs")
    if not isinstance(change["change_id"], str) or any(
        existing.get("change_id") == change["change_id"] for existing in snapshot["changes"]
    ):
        raise ContinuityError("change_id must be unique")
    if change.get("first_person_experience", False):
        raise ContinuityError("cannot promote an import or training artifact to first-person experience")
    if change_class == "evaluated_skill_candidate":
        if change.get("continuity_effect") != "candidate_only":
            raise ContinuityError("skill result cannot auto-install")
        if len(change["evidence_refs"]) < 2:
            raise ContinuityError("skill candidate needs baseline and held-out evaluation evidence")
    else:
        if change.get("continuity_effect") not in {"candidate_only", "record_evidence_only"}:
            raise ContinuityError("unsupported continuity effect")
    result = deepcopy(snapshot)
    result["version"] += 1
    result["changes"].append(deepcopy(change))
    return result
