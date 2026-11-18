"""Synthetic adapter integration checks: mock F.U.C.K.U.P. exports only."""
import sys
import types
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from vera_adapter import AdapterRequest
from vera_adapter.midflight_host import PreparedTurn
from vera_adapter.midflight_fuckup import FuckupPreflightPort


def fake_package(*, revoked=False, bad_readback=False):
    parent = types.ModuleType("fuckup_protocol")
    parent.__path__ = []
    module = types.ModuleType("fuckup_protocol.session_preflight")
    observed = []
    preflight = SimpleNamespace(
        session_id="test-session", correction_id="corr-1",
        correction_revision=2, message_digest="sha256:"+"a"*64,
        source_evidence_ref="synthetic:trusted-readback",
    )
    def load_reference_session_preflight(**kwargs):
        observed.append("load")
        return preflight
    def verify_materialized_prompt(value, messages):
        observed.append("verify_prompt")
        assert messages == [{"role":"developer","content":"synthetic materialized prompt"}]
        return SimpleNamespace(session_id=value.session_id,
                               message_digest=("sha256:"+"0"*64) if bad_readback
                               else value.message_digest)
    def verify_dispatch_currentness(value, *, store, context):
        observed.append("verify_current")
        if revoked and observed.count("verify_current") > 1:
            raise RuntimeError("revoked before delivery")
    module.load_reference_session_preflight = load_reference_session_preflight
    module.verify_materialized_prompt = verify_materialized_prompt
    module.verify_dispatch_currentness = verify_dispatch_currentness
    return {"fuckup_protocol":parent, "fuckup_protocol.session_preflight":module}, observed


class BridgeTests(unittest.TestCase):
    def make_bridge(self, **kwargs):
        return FuckupPreflightPort(
            store=object(), injector=object(), context={"owner":"vera"},
            expected_target="synthetic:correction", operation_id="op-1",
            session_id="test-session", assemble=lambda req,p:
            (req,[{"role":"developer","content":"synthetic materialized prompt"}]), **kwargs)

    def test_calls_canonical_preflight_prompt_and_currentness_twice(self):
        modules, calls=fake_package()
        with patch.dict(sys.modules, modules):
            bridge=self.make_bridge()
            request=AdapterRequest("t1",{},(),())
            prepared=bridge.prepare(request)
            self.assertIsInstance(prepared, PreparedTurn)
            self.assertEqual(prepared.correction_ref, "corr-1@2")
            self.assertTrue(bridge.current(prepared,"dispatch"))
            self.assertTrue(bridge.current(prepared,"delivery"))
            self.assertEqual(calls,["load","verify_prompt","verify_current","verify_current"])

    def test_materialization_mismatch_prevents_prepare(self):
        modules,_=fake_package(bad_readback=True)
        with patch.dict(sys.modules, modules):
            with self.assertRaises(RuntimeError):
                self.make_bridge().prepare(AdapterRequest("t1",{},(),()))

    def test_revocation_is_detected_before_delivery(self):
        modules,_=fake_package(revoked=True)
        with patch.dict(sys.modules, modules):
            bridge=self.make_bridge()
            prepared=bridge.prepare(AdapterRequest("t1",{},(),()))
            self.assertTrue(bridge.current(prepared,"dispatch"))
            with self.assertRaises(RuntimeError):
                bridge.current(prepared,"delivery")

    def test_unknown_preflight_cannot_be_replayed(self):
        modules,_=fake_package()
        with patch.dict(sys.modules, modules):
            bridge=self.make_bridge()
            req=AdapterRequest("t1",{},(),())
            bridge.prepare(req)
            with self.assertRaises(RuntimeError):
                bridge.prepare(req)
