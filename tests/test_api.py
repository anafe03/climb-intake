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
    r = client.post("/tickets/load-samples", params={"fixture": "demo"})
    assert r.status_code == 200 and r.json()["count"] == 32
    cats = {d["extraction"]["category"] for d in r.json()["decisions"]}
    assert {"billing", "bug", "security", "legal_contract", "spam"} <= cats
    assert any(d["extraction"]["escalate"] for d in r.json()["decisions"])


def test_unknown_fixture_is_rejected():
    assert client.post("/tickets/load-samples", params={"fixture": "nope"}).status_code == 400


def test_presenter_notes_are_served():
    r = client.get("/notes")
    assert r.status_code == 200 and "Presenter notes" in r.text
