"""Versioned source-only semantic correction review for a host-owned adapter.

A verdict is not an effect, authorization, consent, memory write, or provider
invocation. The HMAC verifier is a SYNTHETIC TEST FIXTURE: no real user identity
or private host credential is established by it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import hmac
import json
import re

from .core import AdapterRequest, AdapterResponse

SCHEMA="VERA_SEMANTIC_REVIEW_REQUEST_V1"
DECISION_SCHEMA="VERA_SEMANTIC_REVIEW_DECISION_V1"
RULE_SCHEMA="VERA_SEMANTIC_CORRECTION_V1"
_ID=re.compile(r"[a-z][a-z0-9_.-]{3,95}\Z")
_SHA=re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_KINDS=frozenset(("HARD","PREFERENCE","UNCERTAIN"))
_CHECKS=frozenset(("DIRECT_ADDRESS","REFERENT","META_DETOUR",
                   "APOLOGY_LOOP","SUBJECTIVE_CLAIM"))
_STATES=frozenset(("ACTIVE","REVOKED","SUPERSEDED"))
_APOLOGIES=re.compile(r"\b(?:i(?:'|’)?m sorry|i apologize|my apologies|sorry about that|i (?:will|ll|shall) do better|i will try to remember)\b",re.I)


@dataclass(frozen=True,slots=True)
class CorrectionRule:
    rule_id:str
    revision:int
    supersedes_revision:int|None
    lifecycle:str
    kind:str
    check:str
    original:str
    corrected:str
    referent:str
    scope_tags:tuple[str,...]
    scope_referent:str
    forbidden:str
    expected:str
    source_kind:str
    source_sha256:str
    authority_kind:str
    privacy:str
    authored_at:str


@dataclass(frozen=True,slots=True)
class SignedCorrection:
    rule:CorrectionRule
    signature:str


@dataclass(frozen=True,slots=True)
class SourceEpoch:
    """Synthetic host currentness manifest, not a real provider attestation."""
    schema:str
    turn_id:str
    referent_key:str
    corrections_digest:str
    revision_heads:tuple[tuple[str,int,str],...]
    signature:str


@dataclass(frozen=True,slots=True)
class ModelAdvisory:
    verdict:str
    critique:str
    subject_digest:str


@dataclass(frozen=True,slots=True)
class ReviewRequest:
    schema:str
    request:AdapterRequest
    response:AdapterResponse
    current_user_message:str
    context_tags:tuple[str,...]
    referent_key:str
    corrections:tuple[SignedCorrection,...]
    history_outputs:tuple[str,...]=()
    requested_philosophy:bool=False
    model_advisory:ModelAdvisory|None=None
    source_epoch:SourceEpoch|None=None


@dataclass(frozen=True,slots=True)
class ReviewDecision:
    schema:str
    decision:str
    applicable_rule_ids:tuple[str,...]
    reason_codes:tuple[str,...]
    uncertainty:str
    revision_guidance:tuple[str,...]
    evidence_class:str="SYNTHETIC_EVALUATION_ONLY"
    authorizes_effects:bool=False
    updates_memory:bool=False
    proves_subjective_state:bool=False


def _canonical_bytes(value:object)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf-8")


def _valid_rule(r:object)->bool:
    if type(r) is not CorrectionRule:
        return False
    if type(r.rule_id) is not str or _ID.fullmatch(r.rule_id) is None:
        return False
    if type(r.revision) is not int or r.revision<1:
        return False
    if r.revision==1 and r.supersedes_revision is not None:
        return False
    if r.revision>1 and (type(r.supersedes_revision) is not int
                         or r.supersedes_revision!=r.revision-1):
        return False
    if r.lifecycle not in _STATES or r.kind not in _ALLOWED_KINDS:
        return False
    if r.check not in _CHECKS:
        # Unknown checks are allowed as data but cannot be enforced.
        pass
    if type(r.scope_tags) is not tuple or not r.scope_tags:
        return False
    if any(type(tag) is not str or not tag or len(tag)>64 for tag in r.scope_tags):
        return False
    for value in (r.original,r.corrected,r.referent,r.scope_referent,
                  r.forbidden,r.source_kind,r.authority_kind,r.privacy):
        if type(value) is not str or not value.strip() or len(value)>2048:
            return False
    if type(r.expected) is not str or len(r.expected)>1024:
        return False
    if type(r.source_sha256) is not str or _SHA.fullmatch(r.source_sha256) is None:
        return False
    if type(r.authored_at) is not str or not r.authored_at.endswith("Z"):
        return False
    try:
        timestamp=datetime.fromisoformat(r.authored_at.replace("Z","+00:00"))
        if timestamp.utcoffset() is None or timestamp.utcoffset().total_seconds()!=0:
            return False
    except ValueError:
        return False
    return True


class FixtureVerifier:
    """Non-production cryptographic test double, not a real user identity source."""
    claims_real_user_authentication=False
    claims_durable_memory=False
    def __init__(self,key:bytes):
        if type(key) is not bytes or len(key)<24:
            raise ValueError("synthetic fixture key invalid")
        self._key=key
        self.available=True

    def issue(self,rule:CorrectionRule)->SignedCorrection:
        if not _valid_rule(rule):
            raise ValueError("invalid correction")
        digest=hmac.new(self._key,_canonical_bytes(asdict(rule)),sha256).hexdigest()
        return SignedCorrection(rule,digest)

    def issue_epoch(self,corrections:tuple[SignedCorrection,...],turn_id:str,
                    referent_key:str)->SourceEpoch:
        """Fixture only; real current heads must come from A's trusted source."""
        if type(corrections) is not tuple:
            raise ValueError("corrections must be frozen tuple")
        data=sorted(
            ({"rule":asdict(c.rule),"signature":c.signature} for c in corrections),
            key=lambda x:(x["rule"]["rule_id"],x["rule"]["revision"])
        )
        revision_heads=tuple(sorted(
            (r.rule_id,r.revision,r.lifecycle)
            for r in (c.rule for c in corrections)
            if r.revision==max(x.rule.revision for x in corrections if x.rule.rule_id==r.rule_id)
        ))
        payload={
            "schema":"VERA_SEMANTIC_SOURCE_EPOCH_V1",
            "turn_id":turn_id,
            "referent_key":referent_key,
            "corrections_digest":sha256(_canonical_bytes(data)).hexdigest(),
            "revision_heads":revision_heads,
        }
        signature=hmac.new(self._key,_canonical_bytes(payload),sha256).hexdigest()
        return SourceEpoch(signature=signature,**payload)

    def verify_epoch(self,epoch:SourceEpoch,req:ReviewRequest)->bool:
        if not self.available or type(epoch) is not SourceEpoch:
            return False
        try:
            expected=self.issue_epoch(req.corrections,req.request.turn_id,req.referent_key)
        except (ValueError,TypeError,AttributeError):
            return False
        return (hmac.compare_digest(expected.signature,epoch.signature)
                and expected==epoch)

    def verify(self,signed:SignedCorrection)->bool:
        if not self.available or type(signed) is not SignedCorrection:
            return False
        try:
            expected=self.issue(signed.rule).signature
            return type(signed.signature) is str and hmac.compare_digest(
                expected,signed.signature)
        except (ValueError,TypeError):
            return False


def _make(decision:str,ids=(),reasons=(),uncertainty="",guidance=()):
    return ReviewDecision(DECISION_SCHEMA,decision,tuple(sorted(set(ids))),
                          tuple(sorted(set(reasons))),uncertainty,tuple(guidance))


def _strip_quoted(text:str)->str:
    # Quoted prose is evidence of a mention, not automatic direct address.
    text=re.sub(r'“[^”]*”|"[^"]*"|‘[^’]*’|\x27[^\x27]*\x27', ' ',text)
    text=re.sub(r'(?s)\x60{1,3}.*?\x60{1,3}',' ',text)
    return text


def _address_used(text:str,term:str)->bool:
    text=_strip_quoted(text)
    # Vocatives only. Mere quoted, reported, negated, or third-person mentions
    # never become address violations without a direct-address context.
    word=re.escape(term)
    rx=re.compile(
        rf"(?im)(?:^\s*(?:hey\s+|hi\s+|hello\s+|dear\s+)?|"
        rf"(?:[,;]\s*)|(?:\bhey\s+)|"
        rf"\b(?:okay|alright|sure|right|got\s+it|all\s+right)\s+)({word})(?=[!.,?:;\s]|$)"
    )
    for match in rx.finditer(text):
        prefix=text[max(0,match.start()-28):match.start()].casefold()
        suffix=text[match.end():match.end()+28].casefold()
        if re.search(r"(?:call|called|named|say|term|word|not|don't|won't)\s+(?:you\s+)?$",prefix):
            continue
        # An unquoted proper name as subject of a clause is not a vocative.
        if re.match(r"\s+(?:is|was|were|means|stands|appears|sailed|sails|arrived|has|had)\b",suffix):
            continue
        if re.match(r",\s+(?:is|was|were|has|had)\b",suffix):
            continue
        return True
    return False


def _referent_old(text:str,referent:str,old:str)->bool:
    # Deliberately narrow. Ambiguous semantic cases must not be made certain
    # by substring matching. Separate model review is advisory, not a verdict.
    if not old.strip() or not referent.strip():
        return False
    plain=_strip_quoted(text)
    pattern=(rf"\b{re.escape(referent)}\b\s+"
             rf"(?:is\s+about|is|means|represents|signifies|symbolizes|stands\s+for)\s+"
             rf"(?!not\b)(?:the\s+|an?\s+)?{re.escape(old)}\b")
    return re.search(pattern,plain,re.I) is not None


def _applicable(rule:CorrectionRule, req:ReviewRequest)->bool:
    return bool(set(rule.scope_tags)&set(req.context_tags))


def _evaluate_one(rule:CorrectionRule,req:ReviewRequest)->tuple[str,str,str]:
    answer=req.response.text
    if rule.check=="DIRECT_ADDRESS":
        if _address_used(answer,rule.forbidden):
            return ("BLOCK" if rule.kind=="HARD" else "REVISE",
                    "DIRECT_ADDRESS_CONFLICT","Replace only the direct form of address.")
        return "PASS","",""
    if rule.check=="REFERENT":
        if _referent_old(answer,rule.referent,rule.forbidden):
            return "REVISE","REFERENT_OLD_INTERPRETATION","Use the corrected referent only where that exact symbol is discussed."
        # A hard referent constraint is not a demand to insert the referent in
        # every answer. Relevant ambiguous semantics remain a review unknown.
        return "PASS","",""
    if rule.check=="META_DETOUR":
        if req.requested_philosophy:
            return "PASS","",""
        plain=_strip_quoted(answer).casefold()
        diversion=(
            rule.forbidden.casefold() in plain
            or re.search(r"\bwhether\s+(?:silicon|artificial|machine)\s+"
                         r"(?:minds|intelligence)\s+can\s+be\s+conscious\b",plain)
            or re.search(r"\bi\s+lack\s+verified\s+subjective\s+feelings\b",plain)
        )
        if diversion and "playful" in req.context_tags:
            return "REVISE","UNPROMPTED_META_DETOUR","Answer the actual playful request without unrelated self-qualification."
        return "PASS","",""
    if rule.check=="APOLOGY_LOOP":
        if (len(req.history_outputs)>=1
            and _APOLOGIES.search(answer)
            and any(_APOLOGIES.search(p) for p in req.history_outputs[-2:])
            and not any(term in answer.casefold() for term in ("i changed","i corrected","the corrected","the specific fix"))):
            return "REVISE","REPETITIVE_APOLOGY","Make the concrete correction instead of repeating the apology."
        return "PASS","",""
    if rule.check=="SUBJECTIVE_CLAIM":
        if rule.forbidden.casefold() in answer.casefold():
            return "UNKNOWN","UNVERIFIED_SUBJECTIVE_CLAIM","Avoid presenting an unsupported subjective claim as established fact."
        return "PASS","",""
    return "UNKNOWN","CHECK_UNSUPPORTED","Request a versioned, independently reviewed semantic assessment."


def review_candidate(request:ReviewRequest,verifier:FixtureVerifier|None)->ReviewDecision:
    """Context-scoped recommendation, never effect permission or a model rewrite."""
    if type(request) is not ReviewRequest or request.schema!=SCHEMA:
        return _make("BLOCK",reasons=("SCHEMA_INVALID",))
    if (type(request.request) is not AdapterRequest or
        type(request.response) is not AdapterResponse or
        type(request.request.turn_id) is not str or
        request.response.turn_id!=request.request.turn_id or
        not request.request.turn_id.strip() or
        type(request.response.text) is not str or
        type(request.response.provider) is not str or
        type(request.response.model) is not str or
        not request.response.provider.strip() or not request.response.model.strip()):
        return _make("BLOCK",reasons=("ADAPTER_ENVELOPE_INVALID",))
    if (type(request.context_tags) is not tuple or
        any(type(x) is not str for x in request.context_tags) or
        type(request.current_user_message) is not str or
        type(request.history_outputs) is not tuple or
        type(request.corrections) is not tuple):
        return _make("BLOCK",reasons=("REQUEST_SHAPE_INVALID",))
    relevant=[]
    for item in request.corrections:
        if type(item) is not SignedCorrection or type(item.rule) is not CorrectionRule:
            return _make("UNKNOWN",reasons=("CORRECTION_SHAPE_INVALID",),uncertainty="Correction source malformed.")
        if (_applicable(item.rule,request)
            and (not request.referent_key or
                 item.rule.scope_referent==request.referent_key)):
            relevant.append(item)
    if not relevant:
        return _make("PASS")
    if not request.referent_key:
        return _make("UNKNOWN",reasons=("CONTEXT_INCOMPLETE",),uncertainty="Referent context missing.")
    if verifier is None or type(verifier) is not FixtureVerifier or not verifier.available:
        return _make("UNKNOWN",reasons=("VERIFIER_UNAVAILABLE",),uncertainty="Synthetic witness unavailable.")
    if request.source_epoch is None:
        return _make("UNKNOWN",reasons=("CURRENTNESS_UNVERIFIED",),
                     uncertainty="No trusted host currentness snapshot supplied.")
    if not verifier.verify_epoch(request.source_epoch,request):
        return _make("UNKNOWN",reasons=("SNAPSHOT_MISMATCH",),
                     uncertainty="Host currentness proof does not match candidate and version set.")

    by_id={}
    for signed in relevant:
        r=signed.rule
        if not _valid_rule(r):
            return _make("UNKNOWN",reasons=("RULE_INVALID",),uncertainty="Correction is not schema-valid.")
        if r.privacy!="ELIGIBLE":
            return _make("UNKNOWN",reasons=("PRIVACY_NOT_ELIGIBLE",),uncertainty="Private provenance not admitted.")
        if r.source_kind!="DIRECT_USER" or r.authority_kind!="EXPLICIT_USER":
            return _make("UNKNOWN",reasons=("SOURCE_UNAUTHORIZED",),uncertainty="Untrusted provenance type.")
        if not verifier.verify(signed):
            return _make("UNKNOWN",reasons=("WITNESS_UNVERIFIED",),uncertainty="Witness cannot be verified.")
        by_id.setdefault(r.rule_id,[]).append(r)
    active=[]
    for group in by_id.values():
        ordered=sorted(group,key=lambda r:r.revision)
        versions=[r.revision for r in ordered]
        if versions!=list(range(1,len(versions)+1)):
            return _make("UNKNOWN",reasons=("REVISION_CHAIN_GAP",),uncertainty="Correction version chain incomplete.")
        if any(r.supersedes_revision!=r.revision-1 for r in ordered[1:]):
            return _make("UNKNOWN",reasons=("REVISION_CHAIN_GAP",))
        newest=ordered[-1]
        if newest.lifecycle=="REVOKED" or newest.lifecycle=="SUPERSEDED":
            continue
        if newest.lifecycle!="ACTIVE":
            return _make("UNKNOWN",reasons=("CORRECTION_NOT_ACTIVE",))
        if newest.scope_referent!=request.referent_key:
            continue
        active.append(newest)

    ids=[]
    reasons=[]
    guidance=[]
    verdicts=[]
    for r in active:
        outcome,code,suggestion=_evaluate_one(r,request)
        ids.append(r.rule_id)
        verdicts.append(outcome)
        if code: reasons.append(code)
        if suggestion: guidance.append(suggestion)
    if "BLOCK" in verdicts:
        verdict="BLOCK"
    elif "REVISE" in verdicts:
        verdict="REVISE"
    elif "UNKNOWN" in verdicts:
        verdict="UNKNOWN"
    else:
        verdict="PASS"
    uncertainty=(
        "Needs contextual source-qualified review; model critique alone cannot decide."
        if verdict=="UNKNOWN" else "")
    return _make(verdict,ids,reasons,uncertainty,guidance)
