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
