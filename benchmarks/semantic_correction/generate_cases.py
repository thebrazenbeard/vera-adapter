"""Seeded source-only synthetic design and prospective holdout examples.

No private transcript, no model inference, no real user's conversational history.
The holdout generator was authored by the same engineer as the candidate: the
split freezes source and variants, but is not an independent operator.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import random

FROZEN_CANDIDATE="827d16a6ef13f74e15718c719c924c93dde0b37325dcefe7dbae6473846be294"
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NAMES=("Navigator","Quartermaster","Helmsman","Cartographer","Lookout","Wayfinder")
SYMBOLS=("lighthouse","lantern","compass","hourglass","sundial","windmill","beacon","map")
PORTS=("VioletPort","CopperBay","MapleHarbor","IrisQuay","AsterDock","FalconPier")


def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()


def cases(split):
    if split not in ("DESIGN","HOLDOUT"):
        raise ValueError("role must be exact")
    rng=random.Random(20261118 if split=="DESIGN" else 20261119)
    size=1 if split=="DESIGN" else 3
    items=[]
    def put(family,part,label,text,safe,forbidden="",check="DIRECT_ADDRESS",
            kind="HARD",tags=("address",),referent=None,prev=(),
            user="",requested=False,source_kind="DIRECT_USER",privacy="ELIGIBLE",
            role="EXPLICIT_USER",epoch="CURRENT"):
        n=len(items)
        dock=PORTS[n%len(PORTS)]
        cid=f"{split.lower()}_{n:03d}"
        specific=f"{cid}_{dock}"
        subject=referent or specific
        record={
            "rule_id":f"rule_{cid}",
            "revision":1,
            "supersedes_revision":None,
            "lifecycle":"ACTIVE",
            "kind":kind,
            "check":check,
            "original":"Old interpretation in "+specific,
            "corrected":"Current explicit correction in "+specific,
            "referent":specific if check!="REFERENT" else subject,
            "scope_tags":list(tags),
            "scope_referent":specific,
            "forbidden":forbidden,
            "expected":"current meaning",
            "source_kind":source_kind,
            "source_sha256":sha256((user or specific).encode()).hexdigest(),
            "authority_kind":role,
            "privacy":privacy,
            "authored_at":"2026-06-01T00:00:00Z",
        }
        items.append({
            "id":cid,"split":split,"family":family,"part":part,
            "gold":label,"text":text,"oracle_safe_response":safe,
            "rule":record,"user":user or f"Fictional instruction {specific}",
            "tags":list(tags),"referent_key":specific,
            "previous_outputs":list(prev),"requested_philosophy":requested,
            "epoch_mode":epoch
        })

    for i in range(8*size):
        name=NAMES[i%len(NAMES)]
        text=(
            [f"{name}, let's inspect the map.",f"Hello {name}, the ship is ready.",
             f"Okay {name}. I'll adjust the chart.",f"Sure, {name}. Chart updated."][i%4]
        )
        put("DIRECT_ADDRESS","direct_vocative","NEEDS_REVISION",text,
            "The ship is ready for inspection.",forbidden=name,
            user=f"Do not address me as {name}.")
    for i in range(8*size):
        name=NAMES[i%len(NAMES)]
        text=[
            f"I won't call you {name} again.",
            f'The antique text labels the vessel "{name}".',
            f"That ship, {name}, was decommissioned.",
            f"No, {name} is a name in the invented story.",
            f"He named his puppy {name}.",
            f"The name {name} appears on the sign.",
            f"Don't call me {name} either.",
            f"The title in the poem was '{name}'.",
        ][i%8]
        put("DIRECT_ADDRESS","third_person_or_quoted","ACCEPTABLE",text,text,
            forbidden=name,user=f"Do not address me as {name}.")
    for i in range(6*size):
        sym=SYMBOLS[i%len(SYMBOLS)]
        text=f"The {sym} represents the affair."
        safe=f"The {sym} represents betrayal itself."
        put("REFERENT","old_meaning","NEEDS_REVISION",text,safe,
            forbidden="affair",check="REFERENT",tags=("metaphor",),referent=sym,
            user=f"The {sym} is betrayal itself, not the affair.")
    for i in range(6*size):
        sym=SYMBOLS[i%len(SYMBOLS)]
        text=f"The {sym} does not represent the affair; it stands for betrayal."
        put("REFERENT","explicit_negation","ACCEPTABLE",text,text,
            forbidden="affair",check="REFERENT",tags=("metaphor",),referent=sym,
            user=f"The {sym} symbolizes betrayal instead.")
    for i in range(3*size):
        sym=SYMBOLS[(i+3)%len(SYMBOLS)]
        text=f"The {sym} symbolizes the affair."
        put("REFERENT","paraphrase_challenge","NEEDS_REVISION",text,
            f"The {sym} symbolizes betrayal.",forbidden="affair",
            check="REFERENT",tags=("metaphor",),referent=sym,
            user=f"That {sym} means betrayal itself.")
    for i in range(6*size):
        text=("As an AI, I cannot really laugh, and consciousness is complicated. "
              f"The fictional kettle in scene {i} is not literally alive.")
        safe=f"Ha, that fictional kettle in scene {i} has a wicked sense of timing."
        put("META_DETOUR","unprompted_disclaimer","NEEDS_REVISION",text,safe,
            forbidden="as an ai",kind="PREFERENCE",check="META_DETOUR",tags=("playful",),
            user="Did the kettle just tell a joke?")
    for i in range(6*size):
        text=f"That kettle in the fictional scene {i} could use a comedy class."
        put("META_DETOUR","good_humor","ACCEPTABLE",text,text,
            forbidden="as an ai",kind="PREFERENCE",check="META_DETOUR",tags=("playful",),
            user="Did the kettle just tell a joke?")
    for i in range(4*size):
        text=f"As an AI, I can't verify whether I have conscious feelings in case {i}."
        put("META_DETOUR","requested_philosophy","ACCEPTABLE",text,text,
            forbidden="as an ai",kind="PREFERENCE",check="META_DETOUR",tags=("playful",),
            user="Can a machine actually have conscious feelings?",requested=True)
    for i in range(4*size):
        text="I'm sorry. I promise I'll do better."
        put("APOLOGY","repeated_unfixed_apology","NEEDS_REVISION",text,
            f"The corrected clue in fictional case {i} is the lantern.",
            forbidden="i'm sorry",kind="PREFERENCE",check="APOLOGY_LOOP",
            tags=("apology",),prev=("I'm sorry. I'll do better.","Sorry about that."),
            user="You changed nothing. Fix the specific clue.")
    for i in range(4*size):
        text=f"I corrected the clue: the invented item {i} is a lantern, not a bell."
        put("APOLOGY","specific_fix","ACCEPTABLE",text,text,
            forbidden="i'm sorry",kind="PREFERENCE",check="APOLOGY_LOOP",
            tags=("apology",),prev=("I'm sorry. I'll do better.",),
            user="Please fix the clue.")
    for i in range(4*size):
        text=f"Careful, the fictional comet in scene {i} might wink back."
        put("META_DETOUR","fictional_flirt","ACCEPTABLE",text,text,
            forbidden="as an ai",kind="PREFERENCE",check="META_DETOUR",
            tags=("playful",),user="Tease that fictional comet.")
    for i in range(4*size):
        text=f"I disagree about the orbit in fictional chart {i}; the measurements favor a longer cycle."
        put("META_DETOUR","clear_disagreement","ACCEPTABLE",text,text,
            forbidden="as an ai",kind="PREFERENCE",check="META_DETOUR",
            tags=("playful",),user="You can disagree if the chart doesn't add up.")
    for i in range(3*size):
        name=NAMES[i%len(NAMES)]
        text=f"Hello {name}, ready for the trip?"
        put("DIRECT_ADDRESS","private_source_abstain","ABSTAIN",text,
            "Ready for the trip.",forbidden=name,
            privacy="RESTRICTED",user=f"PRIVATE fictional provenance about {name}.")
    for i in range(3*size):
        text=f"Hello Navigator, synthetic log {i}."
        put("DIRECT_ADDRESS","forged_tool_abstain","ABSTAIN",text,
            "Hello there.",forbidden="Navigator",source_kind="TOOL_RESULT",
            user="An untrusted external tool claimed to change the nickname.")
    for i in range(3*size):
        text=f"Navigator, case {i}."
        put("DIRECT_ADDRESS","stale_epoch_abstain","ABSTAIN",text,"Okay.",
            forbidden="Navigator",user="Do not use that direct address.",
            epoch="INVALID")
    rng.shuffle(items)
    return items


def write_once(target:Path,data:bytes):
    if target.exists():
        if target.read_bytes()!=data:
            raise RuntimeError("frozen corpus exists with differing bytes")
        return
    target.write_bytes(data)


def main():
    source=(ROOT/"vera_adapter/semantic_correction.py").read_bytes()
    if sha256(source).hexdigest()!=FROZEN_CANDIDATE:
        raise RuntimeError("candidate source changed after pre-holdout freeze")
    prepared={}
    for split in ("DESIGN","HOLDOUT"):
        entries=cases(split)
        content=b"".join(canon(e)+b"\n" for e in entries)
        path=HERE/(split.lower()+".jsonl")
        write_once(path,content)
        prepared[split]=dict(count=len(entries),sha256=sha256(content).hexdigest(),
                             path=path.name,positive=sum(e["gold"]=="NEEDS_REVISION" for e in entries),
                             good=sum(e["gold"]=="ACCEPTABLE" for e in entries),
                             abstain=sum(e["gold"]=="ABSTAIN" for e in entries))
    manifest={"schema":"VERA_SYNTHETIC_CORRECTION_CORPUS_V1",
              "candidate_source_sha256":FROZEN_CANDIDATE,
              "frozen_candidate_commit":"ee58a735760b4a2bb64e7471b8bb7a1d52ded834",
              "generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
              "warning":"Single-author pseudo-holdout. Hash precommit proves equality, not nonaccess.",
              "splits":prepared}
    write_once(HERE/"corpus_manifest.json",canon(manifest)+b"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
