"""Deterministic, $0 host gate demonstration; never a live model/runtime."""
import json
from vera_adapter import AdapterRequest, AdapterResponse
from vera_adapter.midflight_host import (
    CONTRACT, Concern, Disposition, ReviewVerdict, PreparedTurn, BufferedStream,
    HostGate, InMemoryReplay, InMemoryDelivery, InMemoryAudit, Outcome, digest,
)

class Authority:
    def prepare(self, request):
        return PreparedTurn(request, "NO_ACTIVE_CORRECTION_HOST_CHECKED",
                            "synthetic", digest("synthetic-host"))
    def current(self, _prepared, _phase):
        return True

class Producer:
    def __init__(self, value):
        self.value = value
    def generate(self, _request, _attempt, _hint):
        return self.value

class Reviewer:
    def __init__(self, verdict):
        self.verdict = verdict
    def review(self, _prepared, candidate, attempt):
        return ReviewVerdict(CONTRACT, candidate.turn_id, attempt,
                             digest(candidate.text), self.verdict,
                             "fixture", Concern.HARD, "")

def exercise(turn, producer, verdict):
    delivery = InMemoryDelivery()
    audit = InMemoryAudit()
    gate = HostGate(Authority(), Producer(producer), Reviewer(verdict),
                    delivery, InMemoryReplay(), audit)
    result = gate.run(AdapterRequest(turn, {"name":"Vera"}, (), ()))
    return {
        "outcome": result.outcome.value,
        "delivered_count": len(delivery.records),
        "attempts": result.attempts,
        "candidate_sha256": result.candidate_digest,
        "audited_stages": [row.stage for row in audit.records],
        "private_text_in_audit": any("SECRET_SYNTHETIC" in repr(row) for row in audit.records),
    }

def interrupted():
    yield "SECRET_SYNTHETIC"
    raise IOError("fixture stream interrupted")

def main():
    scenarios = {
        "block": exercise("demo-block",
                          AdapterResponse("demo-block","SECRET_SYNTHETIC","fixture","test"),
                          Disposition.BLOCK),
        "pass": exercise("demo-pass",
                         AdapterResponse("demo-pass","Approved example","fixture","test"),
                         Disposition.PASS),
        "stream_interrupt": exercise("demo-interrupt",
                          BufferedStream("demo-interrupt","fixture","test",interrupted()),
                          Disposition.PASS),
    }
    assert scenarios["block"]["outcome"] == "BLOCKED"
    assert scenarios["block"]["delivered_count"] == 0
    assert scenarios["pass"]["outcome"] == "DELIVERED"
    assert scenarios["pass"]["delivered_count"] == 1
    assert scenarios["stream_interrupt"]["delivered_count"] == 0
    assert all(not item["private_text_in_audit"] for item in scenarios.values())
    print(json.dumps(scenarios,sort_keys=True,indent=2))

if __name__ == "__main__":
    main()
