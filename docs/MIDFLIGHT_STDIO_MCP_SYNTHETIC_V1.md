# Midflight synthetic MCP tool-call probe V1 — Engineer A

**SOURCE ONLY / OFFLINE STDIO / PUBLIC SYNTHETIC FIXTURES / NOT INSTALLED**

This dependency-free Python MCP 2026-07-28 protocol probe uses stdio only. It opens no listener, does not call networks/providers/models, does not fetch private conversations, does not write files, and is not an installed ChatGPT app.

Source: vera_adapter/mcp_synthetic_probe.py; hostile tests: tests/test_mcp_synthetic_probe.py. Owned in vera-adapter draft PR #13. Engineer B's semantic PR #14 stays unmerged and independently owned.

## Tool semantics

The only callable tool is midflight_synthetic_probe; it accepts one enum argument: clean, forbidden or uncertain. **It does not accept candidate text**. Inputs are hardcoded fictional fixtures and the reviewer is a declared synthetic test double, NOT Engineer B's evaluator or a trusted F.U.C.K.U.P. correction source.

Returns typed fixture disposition, candidate SHA-256, an actual *in-process* reviewer invocation observation, and explicit false flags for chatgpt_invocation_observed, final_delivery_verified, authenticated_correction_source, delivered and authorizes_effects. No raw fictional candidate text or private prompt appears in the receipt.

Implements modern server/discover, tools/list, tools/call, and silently accepts one-way notifications. All requests require modern protocol-version metadata; legacy initialize is not implemented. Each newline-delimited JSON-RPC frame is bounded to 8192 bytes; duplicate keys, malformed metadata and arbitrary content fields are rejected without reflecting raw input. The process exits on EOF. There are no real ChatGPT missed-call metrics here.

## Reproduce on isolated Lappy Python 3.12

    py -3.12 -B -m unittest discover -s tests -p test_mcp_synthetic_probe.py -v
    py -3.12 -B -m unittest discover -s tests -p "test_*.py" -v

The tests exercise an actual spawned Python process and three JSON-RPC requests via stdin/stdout. Further tests cover notifications, giant frames, duplicate JSON keys and no candidate reflection. Successful tests show local protocol transport, not live model or ChatGPT integration.

## Release boundary

The actual ChatGPT custom MCP path requires a supported remote endpoint or Secure MCP Tunnel, account/workspace permission, authentication, tool registration and a direct ChatGPT tool invocation. Do NOT open a public endpoint, connect a new plugin, start a service, change credentials/ACLs or install this package without Patrick's separate exact authorization.

Pending: actual tagged text-chat invocations, authenticated correction currentness, Engineer B true semantic qualification, host-observed displayed output, a permission/effect broker, durable replay and independent DriftGuard admission. **RELEASE HOLD.**

Official sources checked November 18, 2026:
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/stdio.mdx
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- https://developers.openai.com/plugins/build/mcp-server
