"""Loopback HTTP wire protocols; translating payloads is not Vera governance."""
from __future__ import annotations
import ipaddress
import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from vera_adapter.provider import ProviderEnvelope


class TransportError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def require_loopback_origin(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if (parsed.scheme != "http" or parsed.username is not None
            or parsed.password is not None or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or parsed.port is None):
        raise ValueError("local HTTP origin with explicit port required")
    try:
        is_loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError as exc:
        raise ValueError("numeric loopback IP required") from exc
    if not is_loopback:
        raise ValueError("nonlocal engine endpoints forbidden")
    return base_url.rstrip("/")


def post_json(url: str, payload: dict, timeout: float) -> dict:
    request = Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=timeout) as result:
            raw = result.read(2_000_001)
    except HTTPError as exc:
        # A rejected redirect is surfaced as HTTPError. Close its body;
        # otherwise Python can warn about an unclosed response stream.
        exc.close()
        raise TransportError("HTTPError") from exc
    except (URLError, OSError) as exc:
        raise TransportError(type(exc).__name__) from exc
    if len(raw) > 2_000_000:
        raise TransportError("engine response size limit exceeded")
    try:
        parsed = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise TransportError("malformed engine JSON") from exc
    if not isinstance(parsed, dict):
        raise TransportError("engine response must be a JSON object")
    return parsed


class LocalChatDriver:
    """Same universal adapter, selectable local wire formats."""
    def __init__(
        self, *, provider: str, model: str, base_url: str,
        protocol: str, timeout: float = 90,
        post: Callable[[str, dict, float], dict] = post_json,
    ):
        if not provider.strip() or not model.strip():
            raise ValueError("missing engine provenance")
        if protocol not in ("ollama_chat", "openai_chat"):
            raise ValueError("unsupported wire protocol")
        if not 0 < timeout <= 600:
            raise ValueError("unbounded timeout")
        self.base_url = require_loopback_origin(base_url)
        self.provider, self.model = provider, model
        self.protocol, self.timeout, self._post = protocol, timeout, post

    def complete(self, envelope: ProviderEnvelope) -> str:
        if not envelope.conversation:
            raise ValueError("no conversation input")
        messages = [{"role": "system", "content": "\n".join(envelope.system_context)}]
        for segment in envelope.conversation:
            if not isinstance(segment, str):
                raise TypeError("conversation items must be strings")
            # Untyped canonical IR segments are user input, never assistant role.
            messages.append({"role": "user", "content": segment})
        payload = {"model": self.model, "messages": messages, "stream": False}
        if self.protocol == "ollama_chat":
            path = "/api/chat"
        else:
            path = "/v1/chat/completions"
        reply = self._post(self.base_url + path, payload, self.timeout)
        if self.protocol == "ollama_chat":
            message = reply.get("message")
        else:
            choices = reply.get("choices")
            message = choices[0].get("message") if isinstance(choices, list) and choices else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise TransportError("no nonempty assistant response")
        return content
