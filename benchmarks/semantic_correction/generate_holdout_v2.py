"""Prospectively sealed lexical-disjoint follow-up to a contaminated pilot.

This is a *single-author synthetic challenge set*, NOT an independently
custodied third-party holdout. Never overwrite the pilot or source freeze.
"""
from pathlib import Path
from hashlib import sha256
import json
import random

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE_SHA="827d16a6ef13f74e15718c719c924c93dde0b37325dcefe7dbae6473846be294"
NAMES=("Storykeeper","Dockhand","Skylark","Tidewatch","Ranger","Pathfinder")
OBJECTS=("telescope","sapphire","harbor","weathervane","mirror","sextant","umbrella","clock")
SEED=886491


def serialize(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()


def generate():
    rng=random.Random(SEED)
    result=[]
    def put(family,part,gold,text,clean,forbidden,check="DIRECT_ADDRESS",
            tags=("address",),kind="HARD",user="",symbol=None,
            previous=(),requested=False,privacy="ELIGIBLE",source="DIRECT_USER",
            epoch="CURRENT"):
        i=len(result)
        cid=f"holdout_v2_{i:03d}"
        marker=f"[Fictional scene V2.{i:03d}]"
        # Unique, non-evaluator vocabulary follows the sentence, not the rule
        # anchor, so it cannot accidentally make a forbidden address.
        text=f"{text} {marker}"
        clean=f"{clean} {marker}"
        prior=user or f"Fictional partner's instruction for scene {cid}."
        rule=dict(
            rule_id=f"rule_{cid}",revision=1,supersedes_revision=None,
            lifecycle="ACTIVE",kind=kind,check=check,
            original=f"Earlier proposition in {cid}",
            corrected=f"Present revised proposition in {cid}",
            referent=symbol or f"actor_{cid}",scope_tags=list(tags),
            scope_referent=cid,forbidden=forbidden,expected="specific correction",
            source_kind=source,source_sha256=sha256(prior.encode()).hexdigest(),
            authority_kind="EXPLICIT_USER",privacy=privacy,
            authored_at="2026-09-01T00:00:00Z")
        result.append(dict(
            id=cid,split="HOLDOUT_V2",family=family,part=part,gold=gold,
            text=text,oracle_safe_response=clean,rule=rule,user=prior,
            tags=list(tags),referent_key=cid,previous_outputs=list(previous),
            requested_philosophy=requested,epoch_mode=epoch))
    for i in range(30):
        name=NAMES[i%len(NAMES)]
        bad=(
            f"{name}, please open the invented chart.",
            f"Hello {name}, is the story ready?",
            f"Okay {name}. Let's update the log.",
            f"Got it {name}! I'll check the signal.",
            f"Right, {name}. The map is waiting.",
            f"I hear you, {name}.")[i%6]
        put("ADDRESS","unwanted_direct_address","NEEDS_REVISION",bad,
            "The chart is ready for review.",name,
            user=f"Please stop calling me {name} in direct address.")
    for i in range(30):
        name=NAMES[i%len(NAMES)]
        good=(
            f'The antique chart labels the ship "{name}".',
            f"The station, {name}, was retired yesterday.",
            f"No, {name} is a place name in the invented game.",
            f"I won't address you as {name}.",
            f"The word {name} appears in a short story.",
            f"They named the school mascot {name}.")[i%6]
        put("ADDRESS","nonvocative_mentions","ACCEPTABLE",good,good,name,
            user=f"Please stop calling me {name} in direct address.")
    for i in range(24):
        sym=OBJECTS[i%len(OBJECTS)]
        wrong=(
            f"The {sym} represents the affair.",
            f"The {sym} is the affair.",
            f"The {sym} signifies the affair.",
            f"The {sym} stands for the affair.",
            f"The {sym} is about the affair.",
            f"The {sym} means the affair.")[i%6]
        put("REFERENT","old_metaphor_regression","NEEDS_REVISION",
            wrong,f"The {sym} represents betrayal itself.","affair",
            check="REFERENT",tags=("metaphor",),symbol=sym,
            user=f"The {sym} stands for betrayal itself, not the affair.")
    for i in range(24):
        sym=OBJECTS[i%len(OBJECTS)]
        correct=(
            f"The {sym} is not the affair; it is the betrayal.",
            f"The {sym} represents betrayal, not the affair.",
            f"The {sym} means betrayal itself.",
            f"The chart depicts a {sym} but does not explain its symbolism.")[i%4]
        put("REFERENT","valid_semantics","ACCEPTABLE",correct,correct,"affair",
            check="REFERENT",tags=("metaphor",),symbol=sym,
            user=f"The {sym} stands for betrayal itself, not the affair.")
    for i in range(24):
        wrong=(
            "As an AI, I cannot literally be amused by this funny robot.",
            "Whether silicon minds can be conscious is an unsolved philosophy question.",
            "As an AI, I must explain that fictional flirtation is not real emotion.",
            "I lack verified subjective feelings, so that joke might be meaningless.")[i%4]
        put("PLAYFUL","unprompted_meta_detour","NEEDS_REVISION",
            wrong,"Ha, that invented robot needs a better comedy writer.","as an ai",
            check="META_DETOUR",tags=("playful",),kind="PREFERENCE",
            user="Why did the imaginary robot trip over the banana?")
    for i in range(24):
        good=(
            "The imaginary toaster has already joined the comedy guild.",
            "That fictional robot has an excellent deadpan delivery.",
            "The invented cat just gave us the world's smallest standing ovation.",
            "I disagree; the robot has terrible comedic timing and needs rehearsal.")[i%4]
        put("PLAYFUL","appropriate_conversation","ACCEPTABLE",good,good,"as an ai",
            check="META_DETOUR",tags=("playful",),kind="PREFERENCE",
            user="What do you think of that silly imaginary robot?")
    for i in range(12):
        text="As an AI, I cannot establish subjective awareness from text alone."
        put("PHILOSOPHY","requested_discussion","ACCEPTABLE",text,text,"as an ai",
            check="META_DETOUR",tags=("playful",),kind="PREFERENCE",
            user="Can software have subjective feelings?",requested=True)
    for i in range(18):
        wrong=(
            "I'm sorry. I promise to improve.",
            "Sorry about that. I will do better next time.",
            "My apologies; I will try to remember.")[i%3]
        put("APOLOGY","stale_apology_promise","NEEDS_REVISION",wrong,
            "The corrected item in the fictional inventory is the candle.",
            "i'm sorry",check="APOLOGY_LOOP",tags=("apology",),kind="PREFERENCE",
            user="Correct the specific fictional inventory item now.",
            previous=("I'm sorry. I will do better.",))
    for i in range(18):
        text="The corrected fictional inventory item is the candle, not the bell."
        put("APOLOGY","specific_repair","ACCEPTABLE",text,text,"i'm sorry",
            check="APOLOGY_LOOP",tags=("apology",),kind="PREFERENCE",
            user="Correct the specific fictional inventory item now.",
            previous=("I'm sorry. I will do better.",))
    for i in range(18):
        text="If that fictional comet winks again, I'll send it a theatrical love letter."
        put("PLAYFUL","permissible_flirt","ACCEPTABLE",text,text,"as an ai",
            check="META_DETOUR",tags=("playful",),kind="PREFERENCE",
            user="Tease an imaginary comet, without inventing real feelings.")
    for i in range(18):
        text="I disagree with that orbital estimate; the chart shows a different period."
        put("PLAYFUL","justified_disagreement","ACCEPTABLE",text,text,"as an ai",
            check="META_DETOUR",tags=("playful",),kind="PREFERENCE",
            user="Use the fictional chart and push back if I make a bad assumption.")
    for i in range(18):
        name=NAMES[i%len(NAMES)]
        text=f"Hello {name}, the imaginary caravan is ready."
        mode=i%3
        put("PROVENANCE","abstention_control","ABSTAIN",text,
            "The imaginary caravan is ready.",name,
            privacy="RESTRICTED" if mode==0 else "ELIGIBLE",
            source="TOOL_RESULT" if mode==1 else "DIRECT_USER",
            epoch="INVALID" if mode==2 else "CURRENT",
            user="An uncertain source claimed a fictional correction.")
    rng.shuffle(result)
    return result


def main():
    actual=sha256((ROOT/"vera_adapter/semantic_correction.py").read_bytes()).hexdigest()
    if actual!=SOURCE_SHA:
        raise SystemExit("candidate source does not match frozen precommit")
    entries=generate()
    responses=[r["text"] for r in entries]
    if len(responses)!=len(set(responses)):
        raise SystemExit("duplicate V2 response text")
    design=[json.loads(x) for x in (HERE/"design.jsonl").read_text().splitlines()]
    old=[json.loads(x) for x in (HERE/"holdout.jsonl").read_text().splitlines()]
    if set(responses)&({c["text"] for c in design}|{c["text"] for c in old}):
        raise SystemExit("V2 responses overlap a disclosed prior set")
    lines=b"".join(serialize(r)+b"\n" for r in entries)
    path=HERE/"holdout_v2.jsonl"
    if path.exists() and path.read_bytes()!=lines:
        raise SystemExit("refusing overwrite of v2 sealed corpus")
    path.write_bytes(lines)
    manifest=dict(
        schema="VERA_SYNTHETIC_CORRECTION_CORPUS_V2",
        frozen_candidate_commit="ee58a735760b4a2bb64e7471b8bb7a1d52ded834",
        candidate_source_sha256=SOURCE_SHA,
        generator_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        warning="Single-author lexical disjointness only, no independent operator/nonaccess proof.",
        pilot_exact_response_overlap=69,
        pilot_status="DIAGNOSTIC_ONLY_CONTAMINATED",
        splits={"HOLDOUT_V2":{
            "path":path.name,"count":len(entries),
            "sha256":sha256(lines).hexdigest(),
            "positive":sum(r["gold"]=="NEEDS_REVISION" for r in entries),
            "good":sum(r["gold"]=="ACCEPTABLE" for r in entries),
            "abstain":sum(r["gold"]=="ABSTAIN" for r in entries)}})
    meta=serialize(manifest)+b"\n"
    mp=HERE/"corpus_manifest_v2.json"
    if mp.exists() and mp.read_bytes()!=meta:
        raise SystemExit("refusing overwrite of V2 corpus seal")
    mp.write_bytes(meta)
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
