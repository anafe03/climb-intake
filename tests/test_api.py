from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_reports_mode():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["mode"] == "rules"


def test_single_ticket_roundtrip_and_explain():
    r = client.post("/tickets", json={"text": "Our CEO is asking why onboarding isn't done. Need progress today."})
    assert r.status_code == 200
    d = r.json()
    assert d["extraction"]["escalate"] is True
    assert d["escalation_queue"] == "human-escalation-desk"
    g = client.get(f"/tickets/{d['id']}")
    assert g.status_code == 200 and g.json()["id"] == d["id"]
    e = client.get(f"/tickets/{d['id']}/explain")
    assert "executive.mention" in e.text


def test_batch_and_samples_and_queues():
    r = client.post("/tickets/load-samples")
    assert r.status_code == 200 and r.json()["count"] == 10
    q = client.get("/queues").json()["queues"]
    assert sum(x["count"] for x in q) >= 10
    lst = client.get("/tickets", params={"queue": "human-escalation-desk"}).json()
    assert len(lst) >= 4  # samples 3, 4, 7, 9 at minimum


def test_upload_txt():
    body = "The export is broken.\n\nRefund invoice #1 please.\n"
    r = client.post("/tickets/upload", files={"file": ("t.txt", body, "text/plain")})
    assert r.status_code == 200 and r.json()["count"] == 2


def test_rejects_empty():
    assert client.post("/tickets", json={"text": ""}).status_code == 422


def test_external_id_is_idempotent():
    body = {"text": "Refund invoice #77 please.", "source": "crm", "external_id": "T-77"}
    a = client.post("/tickets", json=body).json()
    b = client.post("/tickets", json=body).json()
    assert a["id"] == b["id"]
    assert client.get("/queues").json()["total"] == 1


def test_load_samples_twice_does_not_duplicate():
    client.post("/tickets/load-samples")
    client.post("/tickets/load-samples")
    assert client.get("/queues").json()["total"] == 10


def test_low_confidence_goes_to_human_review():
    d = client.post("/tickets", json={"text": "help"}).json()
    assert d["queue"] == "human-review"
    assert d["extraction"]["category_confidence"] < 0.5


def test_upload_csv():
    body = "id,text\n1,The export is broken.\n2,\"Refund invoice #1, please.\"\n"
    r = client.post("/tickets/upload", files={"file": ("t.csv", body, "text/csv")})
    assert r.status_code == 200 and r.json()["count"] == 2
    assert {d["ticket"]["external_id"] for d in r.json()["decisions"]} == {"1", "2"}


def test_demo_fixture_loads_and_covers_the_matrix():
    import json
    from pathlib import Path
    expected = len(json.loads((Path(__file__).resolve().parent.parent / "data" / "demo_tickets.json").read_text()))
    r = client.post("/tickets/load-samples", params={"fixture": "demo"})
    assert r.status_code == 200 and r.json()["count"] == expected
    cats = {d["extraction"]["category"] for d in r.json()["decisions"]}
    assert {"billing", "bug", "security", "legal_contract", "spam"} <= cats
    assert any(d["extraction"]["escalate"] for d in r.json()["decisions"])


def test_unknown_fixture_is_rejected():
    assert client.post("/tickets/load-samples", params={"fixture": "nope"}).status_code == 400


def test_how_it_works_page_is_gone():
    """Dropped on Austin's call. The escalation grid in the pop-out replaces what it tried to explain."""
    assert client.get("/architecture").status_code == 404


def test_recheck_compares_fields_and_persists_nothing():
    """A recheck is a probe, not a decision: it must not route or land in the audit store."""
    r = client.post("/tickets", json={"text": "A former employee still has admin credentials. Our CTO wants answers."})
    d = r.json()
    before = client.get("/queues").json()["total"]
    rows_before = len(client.get("/tickets?limit=100").json())

    rc = client.post(f"/tickets/{d['id']}/recheck?runs=2").json()
    assert rc["runs"] == 2
    # In rules mode the classifier is deterministic, so every field must agree.
    assert rc["stable"] is True
    by = {f["field"]: f for f in rc["fields"]}
    assert by["queue"]["decisive"] and by["queue"]["agree"]
    assert by["category_reason"]["decisive"] is False
    # original + two re-reads
    assert len(by["category"]["values"]) == 3

    assert client.get("/queues").json()["total"] == before
    assert len(client.get("/tickets?limit=100").json()) == rows_before


def test_remove_one_ticket():
    client.delete("/tickets")
    r = client.post("/tickets/load-recorded?fixture=samples").json()
    gone = r["decisions"][0]["id"]
    assert client.delete(f"/tickets/{gone}").status_code == 200
    assert client.get(f"/tickets/{gone}").status_code == 404
    assert client.get("/queues").json()["total"] == r["count"] - 1
    assert client.delete(f"/tickets/{gone}").status_code == 404


def test_recheck_unknown_id_is_404():
    assert client.post("/tickets/nope/recheck").status_code == 404


def test_recheck_run_count_is_capped():
    d = client.post("/tickets", json={"text": "The dark mode toggle resets on refresh."}).json()
    rc = client.post(f"/tickets/{d['id']}/recheck?runs=99").json()
    assert rc["runs"] == 3


def test_recorded_replay_is_instant_and_idempotent(monkeypatch):
    """Replay must not call the model, and loading the same set twice must not duplicate."""
    calls = []
    monkeypatch.setattr("app.pipeline.process", lambda *a, **k: calls.append(1))

    r = client.post("/tickets/load-recorded?fixture=samples")
    assert r.status_code == 200
    first = r.json()
    assert first["count"] == 10
    assert not calls, "replay classified something instead of replaying it"

    # The readings are preserved, the provenance is rewritten.
    d = first["decisions"][0]
    assert d["mode"] == "llm" and d["model"]
    assert d["ticket"]["source"] == "recorded:samples"

    total = client.get("/queues").json()["total"]
    client.post("/tickets/load-recorded?fixture=samples")
    assert client.get("/queues").json()["total"] == total


def test_recorded_unknown_set_says_what_exists():
    r = client.post("/tickets/load-recorded?fixture=nope")
    assert r.status_code == 404 and "samples" in r.json()["detail"]


def test_every_priced_decision_carries_its_cost():
    """Cost is part of the audit record, not a number the UI re-derives from a rate card."""
    from app import pricing
    d = client.post("/tickets", json={"text": "The dark mode toggle resets on refresh."}).json()
    # Rules mode spends nothing, so there is no cost to record.
    assert d["mode"] == "rules" and "cost_usd" not in d["usage"]

    usage = {"input_tokens": 2786, "cache_read_input_tokens": 2607, "output_tokens": 859}
    assert round(pricing.cost_usd(usage, "gpt-5-2025-08-07") * 100, 3) == 0.914
    # A dated id must price as its family, not fall through to the default.
    assert pricing.cost_usd(usage, "gpt-5-mini-2025-08-07") < pricing.cost_usd(usage, "gpt-5")
    assert pricing.cost_usd(usage, "gpt-5-nano-2025-08-07") < pricing.cost_usd(usage, "gpt-5-mini")
    assert pricing.cost_usd({}, "gpt-5") is None


def test_replayed_decisions_are_priced_on_the_way_in():
    client.delete("/tickets")
    r = client.post("/tickets/load-recorded?fixture=samples").json()
    costs = [d["usage"].get("cost_usd") for d in r["decisions"]]
    assert all(c and c > 0 for c in costs), "a replayed decision arrived without its cost"


def test_pricing_serves_the_measured_comparison():
    """The cost card reads this. It went empty once because the file was git- and docker-ignored."""
    r = client.get("/pricing").json()
    models = {m["model"].split("-20")[0] for m in r["models"]}
    assert {"gpt-5", "gpt-5-mini", "gpt-5-nano"} <= models
    nano = next(m for m in r["models"] if m["model"].startswith("gpt-5-nano"))
    assert nano["critical_under_called"], "the disqualifying fact must survive a re-run"


def test_escalation_evidence_shows_the_tickets_behind_recall():
    """The recall number is clickable; this is what the click shows."""
    r = client.get("/evidence/escalation").json()
    names = [g["name"] for g in r["groups"]]
    assert names[-1] == "No keywords at all" and len(names) >= 3
    no_kw = r["groups"][-1]["tickets"]
    # The whole point of the third group: caught, and no keyword rule fired.
    assert no_kw and all(t["caught"] and not t["keywords"] for t in no_kw)


def test_switching_data_sets_keeps_typed_tickets():
    """Loading the 10, the 38 or all of them replaces the examples but keeps what was typed in."""
    client.delete("/tickets")
    typed = client.post("/tickets", json={"text": "The export button does nothing.", "source": "ui"}).json()
    client.post("/tickets/load-recorded?fixture=samples")
    client.delete("/tickets?keep_source=ui")
    left = client.get("/tickets?limit=100").json()
    assert [d["id"] for d in left] == [typed["id"]]


def test_intro_page_sets_the_scene():
    r = client.get("/intro")
    assert r.status_code == 200
    assert "The problem" in r.text
    # the details are pop-ups now, one per decision plus the queues
    for pop in ("who", "what", "urgency", "escalate", "queues"):
        assert f'data-pop="{pop}"' in r.text and f'id="pop-{pop}"' in r.text, pop


def test_explanations_tab_serves_the_one_doc():
    page = client.get("/explanations")
    src = client.get("/explanations.md")
    assert page.status_code == 200 and src.status_code == 200
    assert "## Consistency" in src.text
    # every decision gets its own card, each laid out the same way
    for field in ("Who sent it", "What kind of request", "How urgent", "Escalation", "Where it goes"):
        section = src.text.split("## " + field, 1)[1].split("\n## ", 1)[0]
        for h in ("### How we decide", "### The LLM", "### The keyword check"):
            assert h in section, (field, h)


def test_deliverables_tab_serves_the_pdf():
    assert client.get("/deliverables").status_code == 200
    r = client.get("/deliverables.pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert client.get("/optimization").status_code == 404
