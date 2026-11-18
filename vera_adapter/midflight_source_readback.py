"""Read-only Midflight evidence port: source text is untrusted data, not desire.

No HTTP, credentials, model calls, private-data access, or tool effects.
A host must supply an independently authorized provider/registry. The provider's
identity and the catalog author are not authenticated by this library.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Protocol

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9.-]{0,63}\Z")
_MAX_README_BYTES = 32 * 1024
_MAX_CATALOG_BYTES = 128 * 1024


class SourceHold(ValueError):
    """Insufficient evidence for even a bounded read-only observation."""


def _hex40(v: object) -> bool:
    return isinstance(v, str) and _HEX40.fullmatch(v) is not None


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    name: str
    owner: str
    branch: str
    pinned_head: str
    visibility: str
    role: str

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    repository: str
    path: str
    provider_head: str
    catalog_head: str
    provider_blob_sha: str
    content_sha256: str
    excerpt_untrusted: str
    catalog_status: str
    evidence_class: str = "PROVIDER_OBSERVED_UNAUTHENTICATED"
    source_identity_verified: bool = False
    produces_preferences: bool = False
    establishes_desire: bool = False
    grants_consent: bool = False
    grants_tool_authority: bool = False
    permits_model_training: bool = False
    midflight_reviewer_invoked: bool = False
    final_output_delivered: bool = False


class SourceProvider(Protocol):
    def get_default_head(self, repository: str, branch: str) -> str: ...
    def get_file_at_commit(self, repository: str, path: str, commit: str) -> tuple[bytes, str]: ...


class SourceCatalog:
    """Validate a previously fetched portfolio; no automatic GitHub fetch."""

    def __init__(self, entries: dict[str, CatalogEntry], catalog_digest: str):
        self._entries = dict(entries)
        self.catalog_digest = catalog_digest

    @classmethod
    def from_bytes(cls, raw: bytes, expected_sha256: str, owner: str = "thebrazenbeard") -> "SourceCatalog":
        if not isinstance(raw, bytes) or not 0 < len(raw) <= _MAX_CATALOG_BYTES:
            raise SourceHold("catalog missing or too large")
        if not isinstance(expected_sha256, str) or _HEX64.fullmatch(expected_sha256) is None:
            raise SourceHold("invalid pinned catalog digest")
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_sha256:
            raise SourceHold("catalog digest mismatch")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise SourceHold("catalog is not valid UTF-8 JSON") from exc
        if not isinstance(data, dict) or data.get("schema") != "vera-eros-source-scope/v1":
            raise SourceHold("unsupported catalog schema")
        primary, supplemental = data.get("user_requested"), data.get("supplemental")
        if not isinstance(primary, list) or not isinstance(supplemental, list):
            raise SourceHold("missing typed source lists")
        if not primary or len(primary) + len(supplemental) > 100:
            raise SourceHold("invalid source count")
        entries = {}
        for item in [*primary, *supplemental]:
            if not isinstance(item, dict):
                raise SourceHold("invalid catalog record")
            name, repo_owner = item.get("name"), item.get("owner")
            branch, sha = item.get("branch"), item.get("head_sha")
            visibility, role = item.get("source_visibility"), item.get("role")
            if (not isinstance(name, str) or _NAME.fullmatch(name) is None
                    or repo_owner != owner or branch != "main" or not _hex40(sha)
                    or visibility not in {"public", "private"}
                    or not isinstance(role, str) or not role or len(role) > 64):
                raise SourceHold("invalid or out-of-scope catalog entry")
            key = name.casefold()
            if key in entries:
                raise SourceHold("duplicate source name")
            entries[key] = CatalogEntry(name, repo_owner, branch, sha, visibility, role)
        return cls(entries, actual)

    @property
    def count(self) -> int:
        return len(self._entries)

    def read_public_readme(self, name: str, provider: SourceProvider) -> SourceEvidence:
        """Obtain only a pinned public README; no network client is embedded.

        A provider-claimed head is checked twice to detect common races. This
        cannot authenticate provider identity, detect malicious providers, or
        prevent a host from prompting on untrusted source text as instructions.
        """
        if not isinstance(name, str) or name.casefold() not in self._entries:
            raise SourceHold("repository not in authenticated catalog snapshot")
        entry = self._entries[name.casefold()]
        if entry.visibility != "public":
            raise SourceHold("private source requires separate authentication scope")
        head = provider.get_default_head(entry.repository, entry.branch)
        if not _hex40(head):
            raise SourceHold("provider head is not a commit digest")
        body, declared_blob = provider.get_file_at_commit(entry.repository, "README.md", head)
        if not isinstance(body, bytes) or not 0 < len(body) <= _MAX_README_BYTES:
            raise SourceHold("invalid or oversized source bytes")
        if not _hex40(declared_blob):
            raise SourceHold("invalid Git blob digest")
        calculated = hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
        if calculated != declared_blob:
            raise SourceHold("content differs from provider's Git blob digest")
        if b"\0" in body:
            raise SourceHold("binary content rejected")
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceHold("non-UTF8 source rejected") from exc
        reread_head = provider.get_default_head(entry.repository, entry.branch)
        if reread_head != head:
            raise SourceHold("branch head moved during read")
        return SourceEvidence(
            repository=entry.repository, path="README.md", provider_head=head,
            catalog_head=entry.pinned_head, provider_blob_sha=calculated,
            content_sha256=hashlib.sha256(body).hexdigest(),
            excerpt_untrusted=text[:4096],
            catalog_status=("PROVIDER_HEAD_MATCHES_CATALOG" if head == entry.pinned_head
                            else "CATALOG_STALE_PROVIDER_HEAD_READ"),
        )
