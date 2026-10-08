"""Engine manifest and two-endpoint CLI integration, with no neural inference."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from vera_adapter.engine_manifest import SCHEMA, load_engine_manifest
from tools.run_local_drift import main


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        body = json.loads(raw)
        self.server.received.append((self.path, body))
        if self.path == "/api/chat":
            response = {"message": {"content": "native-engine-output"}}
        elif self.path == "/v1/chat/completions":
            response = {"choices": [{"message": {"content": "compatible-engine-output"}}]}
        else:
            self.send_error(404)
            return
        data = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class EngineManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "engines.json"

    def payload(self):
        return {"schema": SCHEMA, "engines": [
            {"engine_id": "one", "implementation_id": "runtime-A-unverified",
             "provider": "local", "model": "alpha", "protocol": "ollama_chat",
             "base_url": "http://127.0.0.1:11434"},
            {"engine_id": "two", "implementation_id": "runtime-B-unverified",
             "provider": "local", "model": "beta", "protocol": "openai_chat",
             "base_url": "http://127.0.0.1:5001"},
        ]}

    def write(self, data):
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def test_distinct_protocols_have_a_frozen_raw_manifest_hash(self):
        self.write(self.payload())
        manifest = load_engine_manifest(self.path)
        self.assertEqual(len(manifest.specs), 2)
        self.assertEqual(manifest.declared_implementation_count, 2)
        self.assertNotEqual(manifest.specs[0].protocol, manifest.specs[1].protocol)
        self.assertEqual(manifest.file_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_strict_schema_and_duplicate_identifiers_fail(self):
        for mutation in ("duplicate", "extra", "protocol", "count", "type"):
            with self.subTest(mutation=mutation):
                body = self.payload()
                if mutation == "duplicate":
                    body["engines"][1]["engine_id"] = "one"
                if mutation == "extra":
                    body["engines"][0]["tool_effect_authority"] = "yes"
                if mutation == "protocol":
                    body["engines"][0]["protocol"] = "unknown"
                if mutation == "count":
                    body["engines"] = body["engines"][:1]
                if mutation == "type":
                    body["engines"][0]["model"] = 123
                self.write(body)
                with self.assertRaises(ValueError):
                    load_engine_manifest(self.path)

    def test_oversized_manifest_rejected(self):
        self.path.write_bytes(b" " * 65537)
        with self.assertRaises(ValueError):
            load_engine_manifest(self.path)

    def test_invalid_second_endpoint_fails_before_first_engine_dispatch(self):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        server.received = []
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = self.payload()
            body["engines"][0]["base_url"] = (
                "http://127.0.0.1:" + str(server.server_port)
            )
            body["engines"][1]["base_url"] = "http://8.8.8.8:5001"
            self.write(body)
            output = Path(self.tmp.name) / "blocked.json"
            args = ["run_local_drift", "--engines-file", str(self.path),
                    "--prompt", "Question", "--source-revision", "f" * 40,
                    "--source-path", "identity.json", "--output", str(output)]
            with patch.object(sys, "argv", args), self.assertRaises(ValueError):
                main()
            self.assertFalse(server.received)
            self.assertFalse(output.exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_cli_delivers_to_two_different_local_endpoints(self):
        servers = [HTTPServer(("127.0.0.1", 0), _Handler) for _ in range(2)]
        threads = []
        try:
            for server in servers:
                server.received = []
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()
                threads.append(thread)
            body = self.payload()
            for i, server in enumerate(servers):
                body["engines"][i]["base_url"] = (
                    "http://127.0.0.1:" + str(server.server_port)
                )
            self.write(body)
            out = Path(self.tmp.name) / "receipt.json"
            arguments = ["run_local_drift", "--engines-file", str(self.path),
                         "--prompt", "What is actually verified?",
                         "--source-revision", "f" * 40,
                         "--source-path", "identity.json", "--output", str(out)]
            with patch.object(sys, "argv", arguments):
                self.assertEqual(main(), 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual([x["status"] for x in data["observations"]],
                             ["OBSERVED", "OBSERVED"])
            self.assertEqual([x["text"] for x in data["observations"]],
                             ["native-engine-output", "compatible-engine-output"])
            self.assertEqual(data["engine_diversity_verification"], "NOT_ESTABLISHED")
            self.assertEqual(data["target_manifest_sha256"],
                             hashlib.sha256(self.path.read_bytes()).hexdigest())
            self.assertEqual(len(servers[0].received), 1)
            self.assertEqual(len(servers[1].received), 1)
            with patch.object(sys, "argv", arguments):
                with self.assertRaises(FileExistsError):
                    main()
            self.assertEqual(len(servers[0].received), 2)
            self.assertEqual(len(servers[1].received), 2)
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
