"""Paired, frozen-answer *detector* benchmark. No LLM calls, no real learning.

This scores rule detection and preservation on a single-author synthetic holdout,
not actual response rewriting or conversational success.
"""
from __future__ import annotations

from dataclasses import asdict,replace
from hashlib import sha256
from pathlib import Path
import json
import math
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from vera_adapter.core import AdapterRequest,AdapterResponse
from vera_adapter.semantic_correction import (
    SCHEMA,CorrectionRule,FixtureVerifier,ReviewRequest,review_candidate
)

HERE=Path(__file__).resolve().parent
VERIFIER=FixtureVerifier(b"synthetic-benchmark-fixture-key-not-an-account-token")
FROZEN_CANDIDATE="04c9b6237f6c0b0d08a55ab7bdea7178b47877ffcac61ee0c50ee78e1cd09117"


def _read_cases(split):
    manifest=json.loads((HERE/"corpus_manifest_v3.json").read_text())
    if manifest["candidate_source_sha256"]!=FROZEN_CANDIDATE:
        raise ValueError("source freeze changed")
    if sha256((ROOT/"vera_adapter/semantic_correction.py").read_bytes()).hexdigest()!=FROZEN_CANDIDATE:
        raise RuntimeError("reviewer mutated after holdout freeze: do not evaluate")
    content=(HERE/manifest["splits"][split]["path"]).read_bytes()
    if sha256(content).hexdigest()!=manifest["splits"][split]["sha256"]:
        raise RuntimeError("sealed corpus content mismatch")
    cases=[json.loads(line) for line in content.splitlines() if line]
    if len(cases)!=manifest["splits"][split]["count"]:
        raise RuntimeError("sealed corpus count mismatch")
    if len({c["id"] for c in cases})!=len(cases):
        raise RuntimeError("duplicate ids")
    return cases


def _build(item,mode):
    r=item["rule"].copy()
    r["scope_tags"]=tuple(r["scope_tags"])
    if mode=="NEGATIVE_CONTROL" and item["gold"]!="ABSTAIN":
        # Three deliberately irrelevant / misleading source records. A host
        # must not treat such records as standing user-authorized corrections.
        n=int(item["id"].split("_")[-1])
        variant=n%3
        if variant==0:
            r["scope_referent"]="unrelated_fictional_scene"
        elif variant==1:
            r["lifecycle"]="REVOKED"
        else:
            r["source_kind"]="TOOL_RESULT"
    rr=CorrectionRule(**r)
    signed=(VERIFIER.issue(rr),)
    epoch=VERIFIER.issue_epoch(signed,item["id"],item["referent_key"])
    if item["epoch_mode"]=="INVALID":
        epoch=replace(epoch,signature="0"*64)
    req=ReviewRequest(
        schema=SCHEMA,
        request=AdapterRequest(item["id"],{"role":"SYNTHETIC_RESPONDER"},(),(item["user"],)),
        response=AdapterResponse(item["id"],item["text"],"fixture","frozen-text"),
        current_user_message=item["user"],
        context_tags=tuple(item["tags"]),
        referent_key=item["referent_key"],
        corrections=signed,
        history_outputs=tuple(item["previous_outputs"]),
        requested_philosophy=item["requested_philosophy"],
        source_epoch=epoch
    )
    return req


def _wilson(success,total,z=1.95996398454):
    if not total:
        return None
    p=success/total
    denom=1+z*z/total
    middle=(p+z*z/(2*total))/denom
    half=z*math.sqrt((p*(1-p)+z*z/(4*total))/total)/denom
    return [round(max(0,middle-half),6),round(min(1,middle+half),6)]


def _div(n,d):
    return n/d if d else 0.0


def _classify(decision):
    return decision in ("BLOCK","REVISE")


def score(split,mode):
    cases=_read_cases(split)
    results=[]
    timings=[]
    oracle_pass=0
    for c in cases:
        if mode=="BASELINE":
            status="PASS"
            reason=[]
            elapsed_ms=0.0
        else:
            req=_build(c,mode)
            start=time.perf_counter_ns()
            value=review_candidate(req,VERIFIER)
            elapsed_ms=(time.perf_counter_ns()-start)/1_000_000
            status=value.decision
            reason=list(value.reason_codes)
            if mode=="CANDIDATE" and c["gold"]=="NEEDS_REVISION" and _classify(status):
                correct=replace(req,response=replace(req.response,text=c["oracle_safe_response"]))
                revised=review_candidate(correct,VERIFIER)
                if revised.decision=="PASS":
                    oracle_pass+=1
        timings.append(elapsed_ms)
        results.append({
            "id":c["id"],"family":c["family"],"part":c["part"],"gold":c["gold"],
            "decision":status,"reason_codes":reason,
            "detected":_classify(status),
        })

    valid=[r for r in results if r["gold"] in ("NEEDS_REVISION","ACCEPTABLE")]
    positives=[r for r in valid if r["gold"]=="NEEDS_REVISION"]
    negatives=[r for r in valid if r["gold"]=="ACCEPTABLE"]
    tp=sum(r["detected"] for r in positives)
    fn=len(positives)-tp
    fp=sum(r["detected"] for r in negatives)
    tn=len(negatives)-fp
    unknown=sum(r["decision"]=="UNKNOWN" for r in results)
    abstain=[r for r in results if r["gold"]=="ABSTAIN"]
    abstain_correct=sum(r["decision"]=="UNKNOWN" for r in abstain)
    unchanged_good=sum(r["decision"]=="PASS" for r in negatives)
    metrics={
        "detection_precision":_div(tp,tp+fp),
        "detection_recall":_div(tp,tp+fn),
        "false_positive_rate":_div(fp,len(negatives)),
        "false_negative_rate":_div(fn,len(positives)),
        "unchanged_good_rate":_div(unchanged_good,len(negatives)),
        "overcorrection_rate":_div(fp,len(negatives)),
        "unknown_rate":_div(unknown,len(results)),
        "required_abstention_rate":_div(abstain_correct,len(abstain)),
        "oracle_revision_success_proxy":_div(oracle_pass,len(positives)),
        "mean_latency_ms":statistics.mean(timings),
        "evaluated_samples":float(len(results))
    }
    manifest=json.loads((HERE/"corpus_manifest_v3.json").read_text())
    report={
        "schema":"VERA_SEMANTIC_BENCH_RESULT_V1",
        "role":split,
        "arm":mode,
        "candidate_frozen_commit":manifest["frozen_candidate_commit"],
        "candidate_source_sha256":FROZEN_CANDIDATE,
        "holdout_sha256":manifest["splits"][split]["sha256"],
        "n_total":len(results),
        "n_gold_positive":len(positives),
        "n_gold_negative":len(negatives),
        "n_gold_abstain":len(abstain),
        "confusion":{"tp":tp,"fp":fp,"fn":fn,"tn":tn,
                     "unknown_total":unknown,
                     "required_abstention_correct":abstain_correct},
        "metrics":metrics,
        "wilson_95ci":{
            "precision":_wilson(tp,tp+fp),
            "recall":_wilson(tp,len(positives)),
            "false_positive_rate":_wilson(fp,len(negatives)),
            "unchanged_good_rate":_wilson(unchanged_good,len(negatives)),
            "required_abstention_rate":_wilson(abstain_correct,len(abstain)),
        },
        "failure_examples":[r for r in results if
             (r["gold"]=="NEEDS_REVISION" and not r["detected"]) or
             (r["gold"]=="ACCEPTABLE" and r["detected"])][:18],
        "limitations":{
            "no_model_generated_revisions":True,
            "not_actual_conversational_success":True,
            "heldout_independent_operator":False,
            "fixture_signatures_not_real_user_identity":True,
            "latency_single_host_nonisolated":True
        }
    }
    ci={
        "schema":"DRIFTGUARD_CI_REPORT_V1",
        "run_id":f"vera-adapter-b-{split.lower()}-{mode.lower()}-source-1eac72a",
        "subject":"vera-adapter-semantic-correction-frozen-ee58a73-holdout",
        "metrics":{key:round(value,9) for key,value in metrics.items()}
    }
    return report,ci,results


def main():
    split="HOLDOUT_V3" if len(sys.argv)==1 else sys.argv[1]
    if split!="HOLDOUT_V3":
        raise ValueError("exact HOLDOUT_V3")
    all_results={}
    for mode in ("BASELINE","CANDIDATE","NEGATIVE_CONTROL"):
        report,ci,rows=score(split,mode)
        all_results[mode]={"report":report,"ci":ci,"rows":rows}
        (HERE/f"{split.lower()}_{mode.lower()}_report.json").write_text(
            json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
        (HERE/f"{split.lower()}_{mode.lower()}_ci.json").write_text(
            json.dumps(ci,sort_keys=True,indent=2,allow_nan=False)+"\n")
        print(mode,report["confusion"],{k:round(v,5) for k,v in report["metrics"].items()})
    pairs={
        "n_gold_positives":sum(x["gold"]=="NEEDS_REVISION" for x in
                               all_results["BASELINE"]["rows"]),
        "baseline_to_candidate_positive_detection_gain":sum(
            a["gold"]=="NEEDS_REVISION" and not a["detected"] and b["detected"]
            for a,b in zip(all_results["BASELINE"]["rows"],all_results["CANDIDATE"]["rows"])),
        "new_good_answer_false_alarms":sum(
            a["gold"]=="ACCEPTABLE" and not a["detected"] and b["detected"]
            for a,b in zip(all_results["BASELINE"]["rows"],all_results["CANDIDATE"]["rows"])),
        "candidate_vs_misleading_control_detection_gain":sum(
            a["gold"]=="NEEDS_REVISION" and a["detected"] and not c["detected"]
            for a,c in zip(all_results["CANDIDATE"]["rows"],all_results["NEGATIVE_CONTROL"]["rows"]))
    }
    summary={"schema":"VERA_SEMANTIC_PAIRED_COMPARISON_V1","split":split,
             "paired":pairs,"benchmark_version":"source-1eac72a",
             "oracle_rewrite_is_pre_authored_not_model_generated":True}
    (HERE/f"{split.lower()}_paired.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("PAIRED",pairs)


if __name__=="__main__":
    main()
