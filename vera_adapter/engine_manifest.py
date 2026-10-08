"""Frozen, declarative local-engine target configuration.

Different declared implementations are NOT independently verified engines.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "VERA_ADAPTER_LOCAL_ENGINE_TARGETS_V1"


@dataclass(frozen=True)
class LocalEngineSpec:
    engine_id: str
    implementation_id: str
    provider: str
    model: str
    protocol: str
    base_url: str


@dataclass(frozen=True)
class LocalEngineManifest:
    specs: tuple[LocalEngineSpec, ...]
    file_sha256: str

    @property
    def declared_implementation_count(self) -> int:
        return len({spec.implementation_id for spec in self.specs})


def load_engine_manifest(path: Path) -> LocalEngineManifest:
    """Strict parsing; hash raw bytes, don't treat declarations as attestations."""
    source = Path(path)
    if source.stat().st_size > 65536:
        raise ValueError("engine manifest exceeds 64 KiB limit")
    raw = source.read_bytes()
    try:
        data: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("engine manifest is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or set(data) != {"schema", "engines"}:
        raise ValueError("unexpected engine manifest fields")
    if data["schema"] != SCHEMA:
        raise ValueError("unknown engine manifest schema")
    entries = data["engines"]
    if not isinstance(entries, list) or not 2 <= len(entries) <= 8:
        raise ValueError("between two and eight engine targets required")

    specs: list[LocalEngineSpec] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != set(LocalEngineSpec.__dataclass_fields__):
            raise ValueError("engine target fields do not match schema")
        if any(
            not isinstance(entry[key], str) or not entry[key].strip()
            or len(entry[key]) > 512 for key in entry
        ):
            raise ValueError("engine target string invalid")
        if entry["protocol"] not in ("ollama_chat", "openai_chat"):
            raise ValueError("unsupported engine wire protocol")
        specs.append(LocalEngineSpec(**entry))
    if len({x.engine_id for x in specs}) != len(specs):
        raise ValueError("duplicate engine target ID")
    return LocalEngineManifest(
        tuple(specs), hashlib.sha256(raw).hexdigest()
    )
