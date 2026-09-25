"""FastAPI surface: single + batch intake, explain view, queues, audit."""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audit, llm, pipeline, pricing, routing
from .models import Decision, TicketIn

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("climb.api")

DESCRIPTION = """
Ticket intake and routing. Post freeform text, get back a decision you can audit.

**What happens to a ticket.** A model reads it and returns structured fields with a reason for
each one. A layer of plain keyword rules then runs over the *original* text and may raise the
escalation flag or the urgency, never lower either. The routing table in `app/routing.yaml` maps
the result to a queue. Every step is written to SQLite and to a JSON-line audit log before the
response is returned.

**Two modes.** With a provider key set, the model path runs. Without one — or if the model call
fails — the same request is served by the keyword classifier alone and `mode` says so. The API
shape is identical either way, so nothing downstream has to care.

**Idempotency.** `(source, external_id)` is unique. Re-posting a ticket you already sent returns
the original decision rather than classifying it twice.

**Where to start.** `POST /tickets/load-samples` ingests the ten provided tickets in one call,
then `GET /tickets` lists what came out. `GET /tickets/{id}/explain` is the plain-text version of
the same record, meant to be read by a person.
"""

TAGS = [
    {"name": "intake", "description": "Ways in. Every one of these runs the full pipeline and writes an audit record."},
    {"name": "read", "description": "Ways out. Decisions, the human-readable explanation, and queue depths."},
    {"name": "operate", "description": "Health and housekeeping."},
]

app = FastAPI(
    title="Climb Ticket Intake",
    version="0.1.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
)
STATIC = Path(__file__).with_name("static")
DATA = Path(__file__).resolve().parent.parent / "data"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class BatchIn(BaseModel):
    tickets: list[TicketIn]


class BatchOut(BaseModel):
    count: int
    decisions: list[Decision]


def _process_many(tickets: list[TicketIn]) -> list[Decision]:
    workers = int(os.environ.get("BATCH_CONCURRENCY", "4"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(pipeline.process, tickets))


@app.on_event("startup")
def seed_recorded() -> None:
    """Bring the service up with tickets already in it, from a recorded run.

    A demo that opens on an empty page and then classifies ten tickets live spends two minutes
    watching a spinner and bets the first impression on the network. SEED_RECORDED names a set in
    data/recorded; empty string disables it. Only seeds an empty store, so a restart never
    duplicates and a cleared store stays cleared until the process restarts.
    """
    which = os.environ.get("SEED_RECORDED", "").strip()
    if not which:
        return
    try:
        if audit.total():
            return
        loaded = load_recorded(which)
        log.info("seeded %d recorded decisions from '%s'", loaded.count, which)
    except Exception as e:  # never let seeding stop the service from starting
        log.warning("could not seed recorded set '%s': %s", which, e)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/notes", include_in_schema=False)
def presenter_notes():
    """Demo walkthrough. Served from the app so it can deep-link into the live ticket list."""
    return FileResponse(STATIC / "presenter.html")


@app.get("/architecture", include_in_schema=False)
def architecture():
    """Diagrams and decision rules — the page to open when someone asks how it works."""
    return FileResponse(STATIC / "architecture.html")


@app.get("/optimization", include_in_schema=False)
def optimization():
    """Cost, the model comparison, and the one optimisation that pays. Its own page because
    "what does it cost and could it be cheaper" is the second question every client asks."""
    return FileResponse(STATIC / "optimization.html")


@app.get("/health", tags=["operate"], summary="Is it up, and is the model answering?")
def health():
    """`ok` is false when a model is configured but its last call failed.

    The service still answers in that state — on the keyword rules — so a plain 200 would hide a
    real degradation. `mode` tells you which path the next ticket will take.
    """
    last = pipeline.LAST_MODEL_CALL
    degraded = last["status"] == "failing"
    return {
        # ok=False when a model is configured but its last call failed: an orchestrator should be able
        # to tell "up" from "up but answering with the fallback".
        "ok": not degraded,
        "mode": pipeline.effective_mode(),
        "provider": llm.provider(),
        "model": llm.active_model(),
        "last_model_call": last["status"],
        "last_model_error": last["error"],
        "last_model_call_at": last["at"],
    }


@app.post("/tickets", response_model=Decision, tags=["intake"],
          summary="Classify and route one ticket")
def create_ticket(ticket: TicketIn):
    """The main entry point. `text` is the raw ticket; everything else is optional.

    Set `external_id` to whatever your system already calls this ticket and the call becomes safe
    to retry. The response carries the final `extraction`, the model's pre-override answer in
    `llm_extraction`, every rule that fired in `rule_hits`, and the queue it landed in.
    """
    return pipeline.process(ticket)


@app.post("/tickets/batch", response_model=BatchOut, tags=["intake"],
          summary="Classify a list of tickets")
def create_batch(batch: BatchIn):
    """Same processing as `POST /tickets`, run concurrently (`BATCH_CONCURRENCY`, default 4)."""
    decisions = _process_many(batch.tickets)
    return BatchOut(count=len(decisions), decisions=decisions)


@app.post("/tickets/upload", response_model=BatchOut, tags=["intake"],
          summary="Upload a file of tickets")
async def upload(file: UploadFile = File(...)):
    """Batch upload for people who have an export rather than an integration.

    Accepts `.json` (an array of objects with `text`, or of plain strings), `.jsonl`, `.csv` (a
    `text` column, optionally `id` and `source`), or `.txt` split on blank lines.
    """
    raw = (await file.read()).decode("utf-8", errors="replace")
    name = (file.filename or "").lower()
    tickets: list[TicketIn] = []
    try:
        if name.endswith(".jsonl"):
            items = [json.loads(line) for line in raw.splitlines() if line.strip()]
        elif name.endswith(".json"):
            items = json.loads(raw)
        elif name.endswith(".csv"):
            items = list(csv.DictReader(io.StringIO(raw)))
        else:
            items = [block for block in raw.split("\n\n") if block.strip()]
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"could not parse {file.filename}: {e}")
    for item in items:
        if isinstance(item, str):
            tickets.append(TicketIn(text=item.strip(), source=f"upload:{file.filename}"))
        elif isinstance(item, dict) and "text" in item:
            tickets.append(TicketIn(text=item["text"], source=item.get("source", f"upload:{file.filename}"), external_id=item.get("external_id") or item.get("id")))
    if not tickets:
        raise HTTPException(400, "no tickets found in upload")
    decisions = _process_many(tickets)
    return BatchOut(count=len(decisions), decisions=decisions)


FIXTURES = {
    "samples": ("sample_tickets.json", "climb-samples"),
    "demo": ("demo_tickets.json", "demo-set"),
}


@app.post("/tickets/load-samples", response_model=BatchOut, tags=["intake"],
          summary="Ingest a bundled fixture (start here)")
def load_samples(fixture: str = "samples"):
    """Convenience for demos: ingest a bundled ticket fixture.

    - `samples` — the ten provided tickets
    - `demo` — a wider set covering every category, urgency, and escalation reason
    """
    if fixture not in FIXTURES:
        raise HTTPException(400, f"unknown fixture '{fixture}'; expected one of {sorted(FIXTURES)}")
    filename, source = FIXTURES[fixture]
    items = json.loads((DATA / filename).read_text())
    tickets = [TicketIn(text=i["text"], source=source, external_id=str(i["id"])) for i in items]
    decisions = _process_many(tickets)
    return BatchOut(count=len(decisions), decisions=decisions)


RECORDED = Path(__file__).resolve().parent.parent / "data" / "recorded"


@app.post("/tickets/load-recorded", response_model=BatchOut, tags=["intake"],
          summary="Replay decisions from an earlier real run (no new model calls)")
def load_recorded(fixture: str = "samples"):
    """Replays real decisions from a run that already happened. No new model call, no network.

    These are not fixtures or mock answers: every row was produced by the pipeline reading that
    ticket for real, and the model name, token counts, latency and reasoning are the ones from that
    run. What is *not* happening is a fresh call \u2014 the answers were computed earlier and are being
    loaded, the way a database restore loads real rows without re-running the transactions.

    A demo should read *one* ticket live, because that is the part worth watching. Replaying the
    rest removes several minutes of spinner and the risk that a flaky connection decides how the
    presentation goes. These are real decisions from a real run \u2014 recorded by
    `scripts/record_fixture.py`, model and token usage preserved \u2014 not hand-written fixtures.

    `source` is rewritten to `recorded:<set>` so the audit record says where each row came from and
    a replay of the same set twice is idempotent rather than duplicated.
    """
    path = RECORDED / f"{fixture}.json"
    if not path.exists():
        have = sorted(p.stem for p in RECORDED.glob("*.json")) if RECORDED.exists() else []
        raise HTTPException(404, f"no recorded set '{fixture}'; have {have}. Record one with scripts/record_fixture.py")
    payload = json.loads(path.read_text())
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    out: list[Decision] = []
    for raw in payload["decisions"]:
        d = Decision(**raw)
        # Keep the reading; restate when it entered *this* store, so the list orders sensibly and
        # nobody reads a months-old timestamp as a stale decision.
        # Recordings predate the cost field; price them from the usage they already carry.
        usage = dict(d.usage or {})
        if "cost_usd" not in usage:
            c = pricing.cost_usd(usage, d.model)
            if c is not None:
                usage["cost_usd"] = round(c, 6)
        d = d.model_copy(update={
            "id": uuid.uuid4().hex[:12],
            "created_at": now,
            "usage": usage,
            "ticket": d.ticket.model_copy(update={"source": f"recorded:{fixture}"}),
        })
        out.append(audit.record(d))
    return BatchOut(count=len(out), decisions=out)


@app.get("/tickets", response_model=list[Decision], tags=["read"],
         summary="List decisions, newest first")
def list_tickets(limit: int = 100, queue: str | None = None):
    """Pass `queue` to see only what routed to one queue, e.g. `human-escalation-desk`."""
    return audit.list_recent(limit=limit, queue=queue)


@app.get("/tickets/{decision_id}", response_model=Decision, tags=["read"],
         summary="One decision, in full")
def get_ticket(decision_id: str):
    d = audit.get(decision_id)
    if not d:
        raise HTTPException(404, "unknown ticket id")
    return d


@app.get("/tickets/{decision_id}/explain", response_class=PlainTextResponse, tags=["read"],
         summary="The same decision, written for a person")
def explain(decision_id: str):
    """Plain text, not JSON: the four fields, the reason for each, the rules that fired, and any
    override the rules applied to the model's answer. This is what gets pasted into a thread when
    someone asks why a ticket went where it went."""
    d = audit.get(decision_id)
    if not d:
        raise HTTPException(404, "unknown ticket id")
    x = d.extraction
    c = x.customer
    who = c.name or (f"{c.best_guess} (inferred, confidence {c.confidence:.2f})" if c.best_guess else "unknown")
    lines = [
        f"Ticket {d.id}  ({d.created_at}, mode={d.mode}, model={d.model or '-'})",
        "",
        f"  Customer:   {who}",
        f"              ids={c.identifiers or '-'}" + (f"  basis={c.basis}" if c.basis else ""),
        f"              why: {x.customer_reason}",
        f"  Category:   {x.category.value} (confidence {x.category_confidence:.2f})",
        f"              why: {x.category_reason}",
        f"  Urgency:    {x.urgency.value}  signals={x.urgency_signals or '-'}",
        f"              why: {x.urgency_reason}",
        f"  Escalate:   {x.escalate}  reasons={[r.value for r in x.escalation_reasons] or '-'}",
        f"              why: {x.escalation_reason_text}",
        f"  Routed to:  {d.queue}" + (f"  + {d.escalation_queue}" if d.escalation_queue else ""),
        "",
        "Overall rationale:",
        f"  {x.rationale}",
        "",
        "Guardrail rules that fired:",
    ]
    lines += [f"  - {h.rule}: matched '{h.matched}' -> {h.effect}" for h in d.rule_hits] or ["  (none)"]
    if d.overrides:
        lines += ["", "Overrides applied to the model's answer:"] + [f"  - {o}" for o in d.overrides]
    if d.error:
        lines += ["", f"Error during classification: {d.error}"]
    return "\n".join(lines)


class FieldAgreement(BaseModel):
    field: str
    label: str
    decisive: bool  # does this field change where the ticket goes?
    values: list[str]  # index 0 is the original decision, then one per re-read
    agree: bool


class RecheckOut(BaseModel):
    decision_id: str
    runs: int
    fields: list[FieldAgreement]
    stable: bool  # every decisive field agreed
    models: list[str]
    latency_ms: list[int]


def _who(x) -> str:
    c = x.customer
    if c.name:
        return c.name
    return f"(not stated) {c.best_guess}" if c.best_guess else "(not stated)"


# What must be identical is what changes where the ticket goes. Confidence and prose are allowed to
# move, and the response shows that movement rather than scoring it as a failure — claiming a model
# reproduces its own wording is a claim that would not survive the first counter-example.
RECHECK_FIELDS = [
    ("category", "What kind of request", True, lambda d: d.extraction.category.value),
    ("urgency", "How urgent", True, lambda d: d.extraction.urgency.value),
    ("escalate", "Escalate?", True, lambda d: "yes" if d.extraction.escalate else "no"),
    ("escalation_reasons", "Escalated for", True,
     lambda d: ", ".join(sorted(r.value for r in d.extraction.escalation_reasons)) or "—"),
    ("queue", "Where it goes", True,
     lambda d: d.queue + (f" + {d.escalation_queue}" if d.escalation_queue else "")),
    ("customer", "Who sent it", False, lambda d: _who(d.extraction)),
    ("category_confidence", "Category confidence", False,
     lambda d: f"{d.extraction.category_confidence:.2f}"),
    ("customer_confidence", "Customer confidence", False,
     lambda d: f"{d.extraction.customer.confidence:.2f}"),
    ("category_reason", "The wording of the reason", False, lambda d: d.extraction.category_reason),
]


@app.post("/tickets/{decision_id}/recheck", response_model=RecheckOut, tags=["read"],
          summary="Read the same ticket again and compare")
def recheck(decision_id: str, runs: int = 2):
    """Re-runs the classifier on a stored ticket's text and compares the answers field by field.

    Nothing is persisted and nothing is routed: a recheck is a consistency probe, not a decision,
    so it never enters a queue or the audit store. `stable` is true when every field that decides
    where the ticket goes agreed across all reads. Confidence and free text are reported but not
    scored — they are expected to move, and pretending otherwise would be a claim this system
    cannot support.
    """
    original = audit.get(decision_id)
    if not original:
        raise HTTPException(404, "unknown ticket id")
    runs = max(1, min(runs, 3))
    ticket = TicketIn(text=original.ticket.text, source="recheck", external_id=None)
    # Concurrent, because this runs while someone is watching. Sequentially it is the sum of three
    # model calls; in parallel it is the slowest one.
    with ThreadPoolExecutor(max_workers=runs) as ex:
        fresh = list(ex.map(lambda _: pipeline.process(ticket, persist=False), range(runs)))
    everything = [original] + fresh

    fields = []
    for name, label, decisive, get in RECHECK_FIELDS:
        values = [get(d) for d in everything]
        fields.append(FieldAgreement(field=name, label=label, decisive=decisive,
                                     values=values, agree=len(set(values)) == 1))
    return RecheckOut(
        decision_id=decision_id,
        runs=runs,
        fields=fields,
        stable=all(f.agree for f in fields if f.decisive),
        models=[d.model or "keyword rules" for d in everything],
        latency_ms=[d.latency_ms for d in everything],
    )


# data/measured is committed and shipped in the image; data/eval-results is scratch output and is
# ignored by both git and docker. The product only reads from the former.
BAKEOFF = Path(__file__).resolve().parent.parent / "data" / "measured" / "bakeoff.json"


@app.get("/pricing", tags=["read"], summary="What each model measured, per ticket")
def pricing_table():
    """The bake-off results, as measured. No estimation and no extrapolation.

    Every figure here came from running the same 33 gold tickets through that model: the cost is
    computed from the tokens the provider reported, and the error counts are from the same run.
    Shown in the app so "what would a cheaper model cost" is answered next to "what is it costing".
    """
    if not BAKEOFF.exists():
        return {"models": [], "note": "no bake-off on disk; run scripts/model_bakeoff.py"}
    out = []
    for r in json.loads(BAKEOFF.read_text()):
        s = r["summary"]
        out.append({
            "model": r["model"],
            "effort": r.get("effort", "low"),
            "cost_per_ticket": r["cost_per_ticket"],
            "missed_escalations": len(s["missed_escalations"]),
            "false_escalations": len(s["false_escalations"]),
            "urgency_under": len(s.get("urgency_under", [])),
            "critical_under_called": not s.get("urgency_never_under_critical", True),
            "n": r["n"],
        })
    out.sort(key=lambda r: r["cost_per_ticket"] or 0, reverse=True)
    return {"models": out, "measured_on": "the 33-ticket gold set", "running": llm.active_model()}


@app.get("/queues", tags=["read"], summary="Every queue and how deep it is")
def queues():
    """All configured queues, including the ones nothing routed to — an empty queue is a fact
    worth showing, not a row to hide."""
    counts = audit.queue_counts()
    return {"total": audit.total(), "queues": [{"name": q, "count": counts.get(q, 0)} for q in routing.all_queues()]}


@app.delete("/tickets", tags=["operate"], summary="Wipe the audit store")
def clear_all():
    """Clears every decision. Intended for resetting a demo, not for production use."""
    audit.clear()
    return {"ok": True}
