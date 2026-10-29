"""Executable synthetic STM -> Vera Adapter -> MemoryLedger contract tests.

Run with the exact draft sources on PYTHONPATH. The ordinary adapter suite can
still run without the two separately unmerged candidate repositories.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import unittest

try:
    from chatgpt_graph import derive_graph
    from memoryledger.contracts import (
        HostAuthorization, LifecyclePolicy, Purpose, SpeechAct,
    )
except ModuleNotFoundError:
    derive_graph = None

from vera_adapter.history_memoryledger_bridge import (
    HostResolvedEvidence, propose_historical_review,
)


UTC = timezone.utc
SOURCE_SHA = "a" * 64
CONTENT_SHA = hashlib.sha256(b"A synthetic historical preference.").hexdigest()
EVENT_TIME = datetime(2020, 1, 2, 12, 0, tzinfo=UTC)
NOW = datetime(2026, 10, 29, 18, 0, tzinfo=UTC)
PRIVATE_TEST_KEY = b"synthetic-private-locator-key----" + b"x" * 12


@unittest.skipUnless(derive_graph is not None, "requires pinned STM and MemoryLedger draft sources")
class CrossRepoBridgeTests(unittest.TestCase):
    def setUp(self):
        conversation = {
            "id": "synthetic-conversation",
            "current_node": "user-node",
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["user-node"], "message": None},
                "user-node": {
                    "id": "user-node", "parent": "root", "children": [],
                    "message": {
                        "id": "synthetic-message", "author": {"role": "user"},
                        "create_time": EVENT_TIME.timestamp(),
                        "content": {"content_type": "text", "parts": ["A synthetic historical preference."]},
                    },
                },
            },
        }
        graph = derive_graph(conversation, SOURCE_SHA)
        self.node = next(x for x in graph.nodes if x.node_id == "user-node")
        self.binding = HostResolvedEvidence(
            export_sha256=SOURCE_SHA,
            conversation_id="synthetic-conversation", node_id="user-node",
            tenant_id="tenant-synthetic", project_id="project-synthetic",
            identity_id="identity-synthetic", privacy_scope="private-test",
            occurred_at=EVENT_TIME, content_sha256=CONTENT_SHA,
            speech_act=SpeechAct.ASSERTION.value,
            owner_speaker_verified=True, third_party_screened_absent=True,
        )
        self.policy = LifecyclePolicy(historical_review_after=timedelta(days=1))

    def auth(self, event, at, *, revoked=False, wrong_owner=False, current=False):
        return HostAuthorization(
            principal="owner-synthetic", tenant_id=event.tenant_id,
            project_id=event.project_id, identity_id=(
                "identity-foreign" if wrong_owner else event.identity_id
            ),
            conversation_id=event.conversation_id,
            privacy_scopes=(event.privacy_scope,), purposes=(
                (Purpose.CURRENT_REVIEW, Purpose.HISTORICAL_REVIEW)
                if current else (Purpose.HISTORICAL_REVIEW,)
            ),
            consent_ref="consent-synthetic", issued_at=NOW-timedelta(days=1),
            expires_at=NOW+timedelta(days=1), revoked=revoked,
        )

    def plan(self, *, binding=None, node=None, authorize=None, policy=None, key=PRIVATE_TEST_KEY):
        return propose_historical_review(
            self.node if node is None else node,
            resolve_source=lambda _node: self.binding if binding is None else binding,
            authorize=self.auth if authorize is None else authorize,
            private_locator_key=key,
            policy=self.policy if policy is None else policy,
            at=NOW,
        )

    def test_real_stm_graph_to_real_memoryledger_historical_proposal(self):
        result = self.plan()
        self.assertEqual(result.disposition, "REVIEW_HISTORICAL")
        self.assertEqual(result.candidate.source_class, "CHATGPT_ACCOUNT_EXPORT_HISTORICAL")
        self.assertEqual(result.candidate.claim_ceiling,
                         "PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT")
        self.assertNotIn("synthetic-conversation", result.candidate.source_ref)
        self.assertFalse(hasattr(result.candidate, "memory_id"))
        self.assertFalse(hasattr(result.candidate, "ledger_path"))

    def test_assistant_output_cannot_impersonate_owner(self):
        result = self.plan(node=replace(self.node, role="assistant"))
        self.assertEqual((result.disposition, result.reason),
                         ("HOLD", "OWNER_USER_MESSAGE_REQUIRED"))

    def test_untrusted_source_binding_mismatch_denied(self):
        result = self.plan(binding=replace(self.binding, node_id="forged-node"))
        self.assertEqual(result.reason, "SOURCE_BINDING_MISMATCH")

    def test_missing_project_and_unverified_privacy_hold(self):
        self.assertEqual(self.plan(binding=replace(self.binding, project_id=None)).reason,
                         "MISSING_OR_INVALID_HOST_METADATA")
        self.assertEqual(self.plan(binding=replace(self.binding,
                         third_party_screened_absent=False)).reason,
                         "SPEAKER_OR_PRIVACY_UNVERIFIED")
        self.assertEqual(self.plan(binding=replace(self.binding,
                         owner_speaker_verified="true")).reason,
                         "SPEAKER_OR_PRIVACY_UNVERIFIED")

    def test_malformed_node_identity_not_hmac_indexed(self):
        self.assertEqual(self.plan(node=replace(self.node, export_sha256="junk")).reason,
                         "INVALID_SOURCE_IDENTITY")

    def test_missing_and_fabricated_source_timestamp_hold(self):
        self.assertEqual(self.plan(node=replace(self.node, event_time_raw=None)).reason,
                         "EVENT_TIME_UNKNOWN")
        result = self.plan(binding=replace(self.binding, occurred_at=NOW))
        self.assertEqual(result.reason, "EVENT_TIME_SOURCE_MISMATCH")

    def test_wrong_owner_and_revoked_consent_fail_in_memoryledger(self):
        wrong = self.plan(authorize=lambda e, a: self.auth(e, a, wrong_owner=True))
        self.assertEqual(wrong.reason, "HOST_SCOPE_MISMATCH")
        revoked = self.plan(authorize=lambda e, a: self.auth(e, a, revoked=True))
        self.assertEqual(revoked.reason, "CONSENT_NOT_CURRENT")

    def test_current_review_grant_rejected_even_if_host_supplies_it(self):
        result = self.plan(authorize=lambda e, a: self.auth(e, a, current=True))
        self.assertEqual(result.reason, "CURRENT_REVIEW_FORBIDDEN_FOR_IMPORTED_HISTORY")

    def test_archive_does_not_inherit_stm_30_45_expiry(self):
        policy = LifecyclePolicy(historical_review_after=timedelta(days=30),
                                 source_expiry_after=timedelta(days=45))
        self.assertEqual(self.plan(policy=policy).reason,
                         "HISTORICAL_SOURCE_POLICY_REQUIRED")

    def test_no_implicit_historical_review_window(self):
        self.assertEqual(self.plan(policy=LifecyclePolicy()).reason,
                         "EXPLICIT_HISTORICAL_REVIEW_POLICY_REQUIRED")

    def test_correction_needs_verified_ancestry(self):
        b = replace(self.binding, speech_act=SpeechAct.CORRECTION.value,
                    corrects_event_id="cg-synthetic-target")
        self.assertEqual(self.plan(binding=b).reason,
                         "CORRECTION_ANCESTRY_UNVERIFIED")

    def test_quote_and_instruction_are_not_history_assertions(self):
        for speech in (SpeechAct.QUOTE, SpeechAct.INSTRUCTION,
                       SpeechAct.HYPOTHETICAL, SpeechAct.UNKNOWN):
            with self.subTest(speech=speech):
                result = self.plan(binding=replace(self.binding, speech_act=speech.value))
                self.assertEqual(result.reason, "HISTORICAL_SPEECH_ACT_NOT_REVIEWABLE")

    def test_short_or_missing_private_key_fails(self):
        self.assertEqual(self.plan(key=b"too-short").reason,
                         "PRIVATE_LOCATOR_KEY_REQUIRED")

    def test_resolver_and_authorizer_exceptions_fail_closed(self):
        def fail(*_args):
            raise RuntimeError("synthetic host failure")
        result = propose_historical_review(
            self.node, resolve_source=fail, authorize=self.auth,
            private_locator_key=PRIVATE_TEST_KEY, policy=self.policy, at=NOW,
        )
        self.assertEqual(result.reason, "SOURCE_RESOLUTION_FAILED")
        self.assertEqual(self.plan(authorize=fail).reason,
                         "HOST_AUTHENTICATION_REQUIRED")

    def test_private_output_repr_does_not_include_source(self):
        result = self.plan()
        self.assertNotIn("synthetic-conversation", repr(result))
        self.assertNotIn(CONTENT_SHA, repr(result))


if __name__ == "__main__":
    unittest.main()
