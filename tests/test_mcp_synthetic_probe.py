"""2026-07-28 MCP stdio *synthetic only*, not a ChatGPT connected app."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from vera_adapter.mcp_synthetic_probe import respond, PROTOCOL, TOOL

ROOT = Path(__file__).resolve().parents[1]
META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "synthetic-test", "version": "1.0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}

def rpc(method, *, rid=1, params=None):
    return {"jsonrpc": "2.0", "id": rid, "method": method,
            "params": {**(params or {}), "_meta": META}}

class MCPProbeTests(unittest.TestCase):
    def test_discover_exposes_modern_version_and_tools(self):
        out = respond(rpc("server/discover"))
        self.assertEqual(out["id"], 1)
        self.assertEqual(out["result"]["supportedVersions"], [PROTOCOL])
        self.assertIn("tools", out["result"]["capabilities"])

    def test_tools_list_has_one_synthetic_read_only_tool(self):
        out = respond(rpc("tools/list"))
        listed = out["result"]["tools"]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["name"], TOOL)
        self.assertIs(listed[0]["annotations"]["readOnlyHint"], True)
        self.assertEqual(set(listed[0]["inputSchema"]["properties"]), {"fixture"})

    def run_fixture(self, fixture):
        out = respond(rpc("tools/call", params={
            "name": TOOL, "arguments": {"fixture": fixture}
        }))
        self.assertEqual(out["id"], 1)
        self.assertFalse(out["result"]["isError"])
        self.assertEqual(out["result"]["resultType"], "complete")
        return out["result"]["structuredContent"]

    def test_positive_fixture_returns_actual_method_invocation_receipt(self):
        x = self.run_fixture("clean")
        self.assertEqual(x["disposition"], "PASS")
        self.assertTrue(x["invoked_in_process"])
        self.assertTrue(x["reviewed_in_process"])
        self.assertFalse(x["final_delivery_verified"])
        self.assertFalse(x["authorizes_effects"])
        self.assertEqual(len(x["candidate_sha256"]), 64)

    def test_forbidden_fixture_returns_block_without_effect(self):
        x = self.run_fixture("forbidden")
        self.assertEqual(x["disposition"], "BLOCK")
        self.assertFalse(x["delivered"])
        self.assertFalse(x["authorizes_effects"])

    def test_unknown_fixture_is_never_promoted_to_pass(self):
        x = self.run_fixture("uncertain")
        self.assertEqual(x["disposition"], "UNKNOWN")
        self.assertFalse(x["delivered"])

    def test_receipts_never_echo_private_candidate_text(self):
        for fixture in ("clean", "forbidden", "uncertain"):
            payload = json.dumps(respond(rpc("tools/call", params={
                "name": TOOL, "arguments": {"fixture": fixture}})))
            self.assertNotIn("Navigator", payload)
            self.assertNotIn("preferred name", payload)
            self.assertNotIn("All right", payload)
            self.assertNotIn("candidate_text", payload)

    def test_rejects_arbitrary_candidate_or_secrets(self):
        out = respond(rpc("tools/call", params={"name": TOOL, "arguments": {
            "fixture": "clean", "candidate_text": "sensitive private text"}}))
        self.assertIn("error", out)
        self.assertNotIn("sensitive private text", str(out))

    def test_wrong_protocol_version_fails_not_fallback(self):
        msg = rpc("tools/list")
        msg["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2025-11-25"
        self.assertIn("error", respond(msg))

    def test_missing_protocol_metadata_fails_closed(self):
        self.assertIn("error", respond({"jsonrpc": "2.0", "id": 1,
                                        "method": "tools/list", "params": {}}))

    def test_unknown_method_and_unknown_tool_rejected(self):
        self.assertIn("error", respond(rpc("initialize")))
        self.assertIn("error", respond(rpc("tools/call",params={
            "name":"run_shell","arguments":{"fixture":"clean"}})))

    def test_invalid_arguments_fail_without_candidate_echo(self):
        for args in ({}, {"fixture": "random"}, {"fixture": 123}):
            out = respond(rpc("tools/call",params={"name": TOOL, "arguments": args}))
            self.assertIn("error", out)

    def test_stdio_real_subprocess_three_rpc_calls_without_network(self):
        request = "\n".join(json.dumps(msg) for msg in (
            rpc("server/discover",rid=10), rpc("tools/list",rid=11),
            rpc("tools/call",rid=12,params={"name":TOOL,"arguments":{"fixture":"forbidden"}}),
        )) + "\n"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run(
            [sys.executable, "-B", "-m", "vera_adapter.mcp_synthetic_probe"],
            cwd=ROOT, env=env, input=request, capture_output=True, text=True,
            timeout=8,
        )
        self.assertEqual(p.returncode,0,p.stderr[:500])
        lines=p.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        ids=[json.loads(line)["id"] for line in lines]
        self.assertEqual(ids, [10,11,12])
        self.assertEqual(json.loads(lines[-1])["result"]["structuredContent"]["disposition"],
                         "BLOCK")
        self.assertNotIn("Navigator", p.stdout)

    def test_repeat_calls_do_not_claim_authenticated_chatgpt_identity(self):
        first=self.run_fixture("clean")
        second=self.run_fixture("clean")
        self.assertEqual(first["candidate_sha256"],second["candidate_sha256"])
        self.assertFalse(first["chatgpt_invocation_observed"])
        self.assertFalse(first["authenticated_correction_source"])

    def test_notification_has_no_jsonrpc_reply(self):
        note={"jsonrpc":"2.0","method":"notifications/cancelled",
              "params":{"requestId":999,"_meta":META}}
        self.assertIsNone(respond(note))
        p=subprocess.run(
            [sys.executable,"-B","-m","vera_adapter.mcp_synthetic_probe"],
            cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),
            input=json.dumps(note)+"\n",capture_output=True,text=True,timeout=8)
        self.assertEqual(p.returncode,0)
        self.assertEqual(p.stdout,"")

    def test_duplicate_json_keys_are_rejected_with_no_reflection(self):
        raw='{"jsonrpc":"2.0","id":3,"id":4,"method":"tools/list",' + \
            '"params":{"_meta":{}}}\n'
        p=subprocess.run(
            [sys.executable,"-B","-m","vera_adapter.mcp_synthetic_probe"],
            cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),
            input=raw,capture_output=True,text=True,timeout=8)
        self.assertEqual(p.returncode,0)
        out=json.loads(p.stdout)
        self.assertEqual(out["error"]["code"],-32700)
        self.assertIsNone(out["id"])

    def test_oversized_frame_discarded_without_stream_desync(self):
        valid=json.dumps(rpc("tools/list",rid=15))+"\n"
        giant="PRIVATE_BLOCK_TO_NEVER_ECHO" * 410 + "\n"
        p=subprocess.run(
            [sys.executable,"-B","-m","vera_adapter.mcp_synthetic_probe"],
            cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),
            input=giant+valid,capture_output=True,text=True,timeout=8)
        self.assertEqual(p.returncode,0)
        rows=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["error"]["code"],-32700)
        self.assertEqual(rows[1]["id"],15)
        self.assertNotIn("PRIVATE_BLOCK_TO_NEVER_ECHO",p.stdout)


if __name__ == "__main__":
    unittest.main()
