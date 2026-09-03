#!/usr/bin/env python3
"""OpenCode Go requires x-opencode-session (one stable ID per conversation).

Starting 2026-09-06, requests missing it may error. grok-connect's probes use
User-Agent grok-connect/1.0 — the client OpenCode flagged.
"""
import importlib.machinery
import importlib.util
import io
import json
import os
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_cli():
    path = os.path.join(ROOT, "bin", "grok-connect")
    loader = importlib.machinery.SourceFileLoader("grok_connect_cli", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


cli = load_cli()


class FakeResponse:
    def __init__(self, status=200, body=b"{}"):
        self.status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def header_map(req):
    return {k.lower(): v for k, v in req.header_items()}


class NeedsSession(unittest.TestCase):
    def test_opencode_go_pid(self):
        self.assertTrue(cli.needs_opencode_session(pid="opencode-go"))

    def test_opencode_zen_pid(self):
        self.assertTrue(cli.needs_opencode_session(pid="opencode"))

    def test_opencode_host(self):
        self.assertTrue(cli.needs_opencode_session(
            url="https://opencode.ai/zen/go/v1"))
        self.assertTrue(cli.opencode_host("https://opencode.ai/zen/go/v1/chat/completions"))
        self.assertTrue(cli.opencode_host("https://go.opencode.ai/v1"))

    def test_other_providers(self):
        self.assertFalse(cli.needs_opencode_session(pid="deepseek"))
        self.assertFalse(cli.needs_opencode_session(pid="zai-coding-plan"))
        self.assertFalse(cli.needs_opencode_session(
            pid="chatgpt", url="http://127.0.0.1:8788/v1"))
        self.assertFalse(cli.opencode_host("https://api.deepseek.com/chat/completions"))
        self.assertFalse(cli.opencode_host("https://not-opencode.ai/v1"))


class OpencodeHeaders(unittest.TestCase):
    def test_go_url_gets_session_and_client(self):
        h = cli.opencode_headers("https://opencode.ai/zen/go/v1/chat/completions",
                                 session_id="ses-stable")
        self.assertEqual(h["x-opencode-session"], "ses-stable")
        self.assertEqual(h["x-opencode-client"], "grok-connect")

    def test_generates_uuid_when_omitted(self):
        h = cli.opencode_headers("https://opencode.ai/zen/go/v1/chat/completions")
        self.assertRegex(h["x-opencode-session"],
                         r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    def test_other_hosts_get_nothing(self):
        self.assertEqual(cli.opencode_headers("https://api.deepseek.com/v1/chat/completions"), {})
        self.assertEqual(cli.opencode_headers("http://127.0.0.1:8788/v1/responses"), {})


PROVIDER_BLOCK = """\
[auth_provider.opencode-go]
command = "grok-cred opencode-go"

[model_providers.opencode-go]
base_url = "https://opencode.ai/zen/go/v1"
api_backend = "chat_completions"
auth_provider = "opencode-go"

[model.glm-5_2]
model = "glm-5.2"
model_provider = "opencode-go"
name = "glm-5.2 (opencode-go)"
"""

DEEPSEEK_BLOCK = """\
[model_providers.deepseek]
base_url = "https://api.deepseek.com"
api_backend = "chat_completions"
auth_provider = "deepseek"
"""


class ExtraHeadersConfig(unittest.TestCase):
    def test_inserts_when_missing(self):
        text, changed = cli.ensure_opencode_extra_headers(
            PROVIDER_BLOCK, "opencode-go", "ses-1")
        self.assertTrue(changed)
        self.assertIn('x-opencode-session" = "ses-1"', text)
        self.assertIn('x-opencode-client" = "grok-connect"', text)
        # Still valid enough that the next section is intact.
        self.assertIn("[model.glm-5_2]", text)
        self.assertIn('model_provider = "opencode-go"', text)

    def test_idempotent_when_already_present(self):
        once, _ = cli.ensure_opencode_extra_headers(PROVIDER_BLOCK, "opencode-go", "ses-1")
        twice, changed = cli.ensure_opencode_extra_headers(once, "opencode-go", "ses-2")
        self.assertFalse(changed)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("x-opencode-session"), 1)

    def test_merges_into_existing_extra_headers(self):
        cfg = PROVIDER_BLOCK.replace(
            'auth_provider = "opencode-go"\n',
            'auth_provider = "opencode-go"\n'
            'extra_headers = { "X-Keep" = "yes" }\n',
        )
        text, changed = cli.ensure_opencode_extra_headers(cfg, "opencode-go", "ses-m")
        self.assertTrue(changed)
        self.assertIn('"X-Keep" = "yes"', text)
        self.assertIn('x-opencode-session" = "ses-m"', text)

    def test_missing_section_is_noop(self):
        text, changed = cli.ensure_opencode_extra_headers(
            DEEPSEEK_BLOCK, "opencode-go", "ses-1")
        self.assertFalse(changed)
        self.assertEqual(text, DEEPSEEK_BLOCK)

    def test_session_id_from_block(self):
        blk = 'extra_headers = { "x-opencode-session" = "abc-123", "x-opencode-client" = "grok-connect" }'
        self.assertEqual(cli.session_id_from_block(blk), "abc-123")
        self.assertIsNone(cli.session_id_from_block('base_url = "https://opencode.ai/zen/go/v1"'))

    def test_line_format(self):
        line = cli.opencode_extra_headers_line("ses-x")
        self.assertEqual(
            line,
            'extra_headers = { "x-opencode-session" = "ses-x", '
            '"x-opencode-client" = "grok-connect" }',
        )


class ProbeHeaders(unittest.TestCase):
    def _capture(self, base, session_id=None):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = header_map(req)
            captured["body"] = json.loads(req.data.decode())
            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            code, detail = cli.probe(
                base, "chat_completions", "glm-5.2", "tok", session_id=session_id)
        self.assertEqual(code, 200)
        self.assertEqual(detail, "")
        return captured

    def test_opencode_go_probe_sends_session_and_ua(self):
        cap = self._capture("https://opencode.ai/zen/go/v1", session_id="ses-probe")
        h = cap["headers"]
        self.assertEqual(h["user-agent"], "grok-connect/1.0")
        self.assertEqual(h["x-opencode-session"], "ses-probe")
        self.assertEqual(h["x-opencode-client"], "grok-connect")
        self.assertTrue(cap["url"].endswith("/chat/completions"))

    def test_same_id_on_every_model_probe(self):
        ids = []

        def fake_urlopen(req, timeout=None):
            ids.append(header_map(req)["x-opencode-session"])
            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            for model in ("glm-5.2", "kimi-k2.6", "hy3"):
                cli.probe("https://opencode.ai/zen/go/v1", "chat_completions",
                          model, "tok", session_id="one-run")
        self.assertEqual(ids, ["one-run", "one-run", "one-run"])

    def test_deepseek_probe_has_ua_but_no_opencode_session(self):
        cap = self._capture("https://api.deepseek.com")
        h = cap["headers"]
        self.assertEqual(h["user-agent"], "grok-connect/1.0")
        self.assertNotIn("x-opencode-session", h)
        self.assertNotIn("x-opencode-client", h)

    def test_http_error_still_sent_the_header(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = header_map(req)
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", hdrs=None, fp=io.BytesIO(b"nope"))

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            code, detail = cli.probe(
                "https://opencode.ai/zen/go/v1", "chat_completions", "glm-5.2", "tok",
                session_id="ses-err")
        self.assertEqual(code, 401)
        self.assertEqual(captured["headers"]["x-opencode-session"], "ses-err")
        self.assertIn("nope", detail)


if __name__ == "__main__":
    unittest.main()
