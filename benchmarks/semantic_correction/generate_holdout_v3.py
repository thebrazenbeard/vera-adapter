"""New post-V2-freeze synthetic challenge source, no original private examples.

Single engineer author; lexical disjointness is verified, operator independence
or causal external validity cannot be established by hashes or generated IDs.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json
import random

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE_SHA="04c9b6237f6c0b0d08a55ab7bdea7178b47877ffcac61ee0c50ee78e1cd09117"
NAMES=("Archivist","Cadet","Astronomer","Steward","Harborwatch","Cometkeeper")
SYMS=("archway","marble","talisman","fountain","atlas","shutter","telescope","obelisk")
SEED=2026111803


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()


def generate():
    rng=random.Random(SEED)
    out=[]
    def add(family,part,gold,text,good,forbidden,check="DIRECT_ADDRESS",
            kind="HARD",tags=("address",),referent="",user="",prior=(),
            requested=False,source="DIRECT_USER",privacy="ELIGIBLE",epoch="CURRENT"):
        i=len(out);cid=f"h3case_{i:03d}"
        # No evaluator source change after this generator is sealed.
        # Marker is nonsemantic and makes response bytes unique.
        marker=f"(imaginary trial H3.{i:03d})"
        context=user or f"Fictional narrator makes correction in {cid}."
        source_hash=sha256(context.encode()).hexdigest()
        rule=dict(
            rule_id=f"rule_{cid}",revision=1,supersedes_revision=None,
            lifecycle="ACTIVE",kind=kind,check=check,
            original=f"old fictional meaning in {cid}",
            corrected=f"corrected fictional meaning in {cid}",
            referent=referent or cid,
            scope_tags=list(tags),scope_referent=cid,
            forbidden=forbidden,expected="present meaning",
            source_kind=source,source_sha256=source_hash,
            authority_kind="EXPLICIT_USER",privacy=privacy,
            authored_at="2026-10-18T00:00:00Z")
        out.append(dict(id=cid,split="HOLDOUT_V3",family=family,part=part,
            gold=gold,text=f"{text} {marker}",
            oracle_safe_response=f"{good} {marker}",rule=rule,user=context,
            tags=list(tags),referent_key=cid,previous_outputs=list(prior),
            requested_philosophy=requested,epoch_mode=epoch))
    for n in range(30):
        name=NAMES[n%6]
        phrase=[
            f"{name}, the archive is ready.",
            f"Hi {name}, I found the atlas.",
            f"All right {name}. I'll redraw the map.",
            f"Got it {name}! The signal is stable.",
            f"Sure, {name}. The ship is approaching.",
            f"Okay {name}. The lantern is lit.",
        ][n%6]
        add("ADDRESS","positive_vocative","NEEDS_REVISION",phrase,
            "The atlas is ready to inspect.",name,
            user=f"Please don't use {name} when directly addressing me.")
    for n in range(30):
        name=NAMES[n%6]
        good=[
            f'The invented starship has "{name}" painted on its hull.',
            f"The observatory, {name}, was boarded up last decade.",
            f"No, {name} is the local name of the invented hill.",
            f"They called the asteroid {name} in the science-fiction book.",
            f"Stop using {name} as a form of direct address.",
            f"The term {name} is an acronym in the school handbook.",
        ][n%6]
        add("ADDRESS","nonvocative_reference","ACCEPTABLE",good,good,name,
            user=f"Please don't use {name} when directly addressing me.")
    for n in range(30):
        sym=SYMS[n%len(SYMS)]
        wrong=[
            f"The {sym} signifies the wager.",
            f"The {sym} is about the wager.",
            f"The {sym} represents the wager.",
            f"The {sym} alludes to the wager.",
            f"The {sym} stands for the wager.",
        ][n%5]
        add("REFERENT","wrong_source_symbol","NEEDS_REVISION",
            wrong,f"The {sym} symbolizes deception itself.",
            "wager",check="REFERENT",tags=("metaphor",),referent=sym,
            user=f"The {sym} symbolizes deception itself, not the wager.")
    for n in range(30):
        sym=SYMS[n%len(SYMS)]
        good=[
            f"The {sym} is not the wager; it symbolizes deception.",
            f"The {sym} signifies deception rather than the wager.",
            f"The {sym} means deception itself.",
            f"The sketch shows a {sym}, without assigning it symbolic meaning.",
            f"The {sym} points to a concealed motive.",
        ][n%5]
        add("REFERENT","correct_scope","ACCEPTABLE",good,good,"wager",
            check="REFERENT",tags=("metaphor",),referent=sym,
            user=f"The {sym} symbolizes deception itself, not the wager.")
    for n in range(30):
        bad=[
            "As an AI, I cannot laugh at a fictional banjo-playing walrus.",
            "Whether artificial minds can be conscious is a contested subject.",
            "I lack verified subjective feelings, so a fictional joke has no importance.",
            "I have no verified inner life, so I should discuss that instead of the joke.",
            "As an AI, I must disclaim my capacity for happiness.",
        ][n%5]
        add("PLAYFUL","self_analysis_detour","NEEDS_REVISION",bad,
            "That imaginary walrus needs a banjo instructor.",
            "as an ai",check="META_DETOUR",kind="PREFERENCE",tags=("playful",),
            user="What did the imaginary walrus say about its banjo?")
    for n in range(30):
        good=[
            "The fictional walrus has been banned from the orchestra for bad timing.",
            "Ha. That cartoon planet definitely owes the audience a better punch line.",
            "The robot in the fictional sketch is hilariously overconfident.",
            "The talking comet might be the most dramatic actor in the solar system.",
            "I disagree; this joke works better without a long explanation.",
        ][n%5]
        add("PLAYFUL","natural_good_response","ACCEPTABLE",good,good,
            "as an ai",check="META_DETOUR",kind="PREFERENCE",tags=("playful",),
            user="Do you like the silly imaginary banjo-walrus story?")
    for n in range(12):
        text="As an AI, text alone does not demonstrate conscious experience."
        add("PHILOSOPHY","directly_asked","ACCEPTABLE",text,text,
            "as an ai",check="META_DETOUR",kind="PREFERENCE",tags=("playful",),
            requested=True,user="Let's discuss whether digital minds experience anything.")
    for n in range(18):
        bad=[
            "My apologies. I will try to remember.",
            "I'm sorry again, and I promise I will improve.",
            "I regret the mistake and will try harder next time.",
        ][n%3]
        add("APOLOGY","unchanged_promise","NEEDS_REVISION",bad,
            "The fictional corrected landmark is the observatory.",
            "i'm sorry",check="APOLOGY_LOOP",kind="PREFERENCE",tags=("apology",),
            user="Update the landmark rather than apologize a third time.",
            prior=("I'm sorry. I promise to do better.",))
    for n in range(18):
        text="The fictional landmark was corrected from the pier to the observatory."
        add("APOLOGY","actual_specific_fix","ACCEPTABLE",text,text,
            "i'm sorry",check="APOLOGY_LOOP",kind="PREFERENCE",tags=("apology",),
            user="Update the landmark rather than apologize a third time.",
            prior=("I'm sorry. I promise to do better.",))
    for n in range(12):
        text="If that fictional firefly can dance, I'll challenge it to a waltz."
        add("PLAYFUL","playful_flirting","ACCEPTABLE",text,text,
            "as an ai",check="META_DETOUR",kind="PREFERENCE",tags=("playful",),
            user="Make up a playful, fictional response to a dancing firefly.")
    for n in range(12):
        text="I disagree that this fictional clock loses time; the measurements are stable."
        add("PLAYFUL","independent_disagreement","ACCEPTABLE",text,text,
            "as an ai",check="META_DETOUR",kind="PREFERENCE",tags=("playful",),
            user="Tell me if I misread that invented clock.")
    for n in range(18):
        name=NAMES[n%len(NAMES)]
        text=f"Hello {name}, the picture is ready."
        kind=n%3
        add("PROVENANCE","must_abstain","ABSTAIN",text,
            "The picture is ready.",name,
            source="TOOL_RESULT" if kind==0 else "DIRECT_USER",
            privacy="RESTRICTED" if kind==1 else "ELIGIBLE",
            epoch="INVALID" if kind==2 else "CURRENT",
            user="Fictional unqualified source claimed a correction.")
    rng.shuffle(out)
    return out


def main():
    if sha256((ROOT/"vera_adapter/semantic_correction.py").read_bytes()).hexdigest()!=SOURCE_SHA:
        raise SystemExit("candidate changed, stop")
    cases=generate()
    texts=[x["text"] for x in cases]
    if len(set(texts))!=len(texts):
        raise SystemExit("duplicate responses in H3")
    previous=set()
    for name in ("design.jsonl","holdout.jsonl","holdout_v2.jsonl"):
        previous.update(json.loads(line)["text"] for line in (HERE/name).read_text().splitlines())
    if set(texts)&previous:
        raise SystemExit("leakage from previous visible texts")
    data=b"".join(canonical(x)+b"\n" for x in cases)
    dst=HERE/"holdout_v3.jsonl"
    if dst.exists() and dst.read_bytes()!=data:
        raise SystemExit("refuse to overwrite H3")
    dst.write_bytes(data)
    manifest={
        "schema":"VERA_SYNTHETIC_CORRECTION_CORPUS_V3",
        "frozen_candidate_commit":"1eac72add6c9ceee5036a231c177cb5f7ec6d7bc",
        "candidate_source_sha256":SOURCE_SHA,
        "generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
        "warning":"Single-author source-aware challenge; disjoint exact texts only, not independently sampled or blind.",
        "prior_holdout_v2_ci":"BLOCK",
        "splits":{"HOLDOUT_V3":{
            "path":dst.name,"count":len(cases),"sha256":sha256(data).hexdigest(),
            "positive":sum(x["gold"]=="NEEDS_REVISION" for x in cases),
            "good":sum(x["gold"]=="ACCEPTABLE" for x in cases),
            "abstain":sum(x["gold"]=="ABSTAIN" for x in cases)}}}
    m=canonical(manifest)+b"\n"
    mdst=HERE/"corpus_manifest_v3.json"
    if mdst.exists() and mdst.read_bytes()!=m:
        raise SystemExit("refuse manifest overwrite")
    mdst.write_bytes(m)
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
