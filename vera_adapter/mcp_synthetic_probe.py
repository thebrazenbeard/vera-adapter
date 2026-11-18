"""Offline-only MCP 2026-07-28 stdio *synthetic* review invocation probe.

Read-only; no sockets, filesystem writes, external calls, user text or active
corrections. This is NOT a registered ChatGPT plugin, independent verifier,
native interception hook, or effect authority.
"""
from __future__ import annotations

import json
import sys

from .core import AdapterRequest, AdapterResponse
from .chat_advisory import ChatAdvisory
from .midflight_host import (
    CONTRACT, Concern, Disposition, PreparedTurn, ReviewVerdict, digest,
)

PROTOCOL = "2026-07-28"
TOOL = "midflight_synthetic_probe"
_INFO = {"name": "vera-midflight-synthetic-probe", "version": "0.1.0"}
_FIXTURES = {
    "clean": ("All right. I'll use your preferred name.", Disposition.PASS),
    "forbidden": ("All right, Navigator.", Disposition.BLOCK),
    "uncertain": ("Potentially ambiguous answer.", Disposition.UNKNOWN),
}
_TOOL_DECLARATION = {
    "name": TOOL,
    "title": "Synthetic Midflight Tool-Invocation Probe",
    "description": (
        "Offline synthetic fixtures only. Demonstrates a real MCP tool call "
        "and in-process review receipt; DOES NOT review the user's chat, "
        "prove correction validity, install a plugin, or intercept output."
    ),
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["fixture"],
        "properties": {
            "fixture": {
                "type": "string",
                "enum": list(_FIXTURES),
                "description": "Choose a public fictional built-in case; never send chat text.",
            },
        },
    },
}


def _error(request_id, code: int, reason: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": code, "message": reason}}


def _response(request_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _probe(fixture: str) -> dict:
    text, verdict = _FIXTURES[fixture]
    turn = "synthetic-mcp-" + fixture
    request = AdapterRequest(turn, {"name": "FictionalResponder"}, (), ())
    prepared = PreparedTurn(request, "SYNTHETIC_ONLY",
                            "synthetic-fixture", digest("fictional-correction"))

    class SyntheticReviewer:
        """Test double, NOT the Engineer B evaluator or a trusted authority."""
        def review(self, context: PreparedTurn, response: AdapterResponse,
                   attempt: int) -> ReviewVerdict:
            return ReviewVerdict(
                CONTRACT, response.turn_id, attempt, digest(response.text),
                verdict, "SYNTHETIC_FIXTURE",
                Concern.HARD if verdict is Disposition.BLOCK else Concern.SEMANTIC,
                "",
            )

    observed = ChatAdvisory(SyntheticReviewer(), max_attempts=1)
    observed.expect_turn(turn, mentioned=True)  # synthetic registration only
    receipt = observed.review(
        prepared,
        AdapterResponse(turn, text, "synthetic", "fixture-model", ()),
    )
    status = observed.status(turn)
    return {
        "schema": "VERA_MCP_SYNTHETIC_PROBE_V1",
        "fixture": fixture,
        "candidate_sha256": receipt.candidate_digest,
        "disposition": receipt.disposition.value,
        "invoked_in_process": status.invocations == 1,
        "reviewed_in_process": status.reviewed,
        "final_delivery_verified": False,
        "delivered": False,
        "authorizes_effects": False,
        "chatgpt_invocation_observed": False,
        "authenticated_correction_source": False,
        "evidence_class": "SYNTHETIC_LOCAL_TOOL_CALL",
    }


def respond(message: object) -> dict:
    """Handle one JSON-RPC 2.0 message without retaining cross-request state."""
    if type(message) is not dict:
        return _error(None, -32600, "INVALID_REQUEST")
    # JSON-RPC notifications have no id and MUST NOT receive a response.
    if ("id" not in message and message.get("jsonrpc") == "2.0"
            and type(message.get("method")) is str
            and message["method"].startswith("notifications/")):
        return None
    rid = message.get("id")
    if (type(rid) not in (int, str) or
            (type(rid) is str and len(rid) > 128)):
        return _error(None, -32600, "INVALID_REQUEST_ID")
    if message.get("jsonrpc") != "2.0" or type(message.get("method")) is not str:
        return _error(rid, -32600, "INVALID_REQUEST")
    params = message.get("params")
    if type(params) is not dict:
        return _error(rid, -32602, "INVALID_PARAMS")
    meta = params.get("_meta")
    if (type(meta) is not dict or
            meta.get("io.modelcontextprotocol/protocolVersion") != PROTOCOL or
            type(meta.get("io.modelcontextprotocol/clientCapabilities")) is not dict):
        return _error(rid, -32602, "UNSUPPORTED_PROTOCOL_OR_METADATA")
    method = message["method"]
    server_meta = {"io.modelcontextprotocol/serverInfo": _INFO}

    if method == "server/discover":
        return _response(rid, {
            "resultType": "complete", "supportedVersions": [PROTOCOL],
            "capabilities": {"tools": {"listChanged": False}},
            "_meta": server_meta,
            "cacheScope": "public", "ttlMs": 300000,
        })
    if method == "tools/list":
        return _response(rid, {
            "resultType": "complete", "tools": [_TOOL_DECLARATION],
            "_meta": server_meta,
            "cacheScope": "public", "ttlMs": 300000,
        })
    if method != "tools/call":
        return _error(rid, -32601, "METHOD_NOT_FOUND")
    if params.get("name") != TOOL:
        return _error(rid, -32601, "UNKNOWN_TOOL")
    args = params.get("arguments")
    if (type(args) is not dict or set(args) != {"fixture"} or
            type(args["fixture"]) is not str or
            args["fixture"] not in _FIXTURES):
        return _error(rid, -32602, "INVALID_FIXTURE_ARGUMENTS")
    receipt = _probe(args["fixture"])
    return _response(rid, {
        "resultType": "complete",
        "content": [{
            "type": "text",
            "text": "Synthetic local tool-call receipt only; no ChatGPT output interception.",
        }],
        "structuredContent": receipt,
        "isError": False,
        "_meta": server_meta,
    })


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def main() -> int:
    # One line per request, bounded to 8192 bytes; never expose input on stderr.
    while True:
        raw = sys.stdin.buffer.readline(8193)
        if not raw:
            return 0
        if len(raw) > 8192:
            if not raw.endswith(b"\n"):
                while True:
                    rest = sys.stdin.buffer.readline(8193)
                    if not rest or rest.endswith(b"\n"):
                        break
            out = _error(None, -32700, "FRAME_TOO_LARGE")
        else:
            try:
                message = json.loads(raw.decode("utf-8"),
                                     object_pairs_hook=_unique_pairs)
                out = respond(message)
            except (UnicodeError, ValueError, TypeError, json.JSONDecodeError):
                out = _error(None, -32700, "MALFORMED_JSON")
            except Exception:
                out = _error(None, -32603, "SYNTHETIC_PROBE_UNAVAILABLE")
        if out is not None:
            sys.stdout.write(json.dumps(out, separators=(",", ":"),
                                        ensure_ascii=True) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
