"""FastAPI surface: single + batch intake, explain view, queues, audit."""
from __future__ import annotations

import csv
import io
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audit, llm, pipeline, routing
from .models import Decision, TicketIn

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="Climb Ticket Intake", version="0.1.0")
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


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "mode": pipeline.effective_mode(), "provider": llm.provider(), "model": llm.active_model()}


@app.post("/tickets", response_model=Decision)
def create_ticket(ticket: TicketIn):
    return pipeline.process(ticket)


@app.post("/tickets/batch", response_model=BatchOut)
def create_batch(batch: BatchIn):
    decisions = _process_many(batch.tickets)
    return BatchOut(count=len(decisions), decisions=decisions)


@app.post("/tickets/upload", response_model=BatchOut)
async def upload(file: UploadFile = File(...)):
    """Accepts .json (array of {text,...} or strings), .jsonl, .csv (a `text` column, optional id/source), or .txt (blank-line separated)."""
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


@app.post("/tickets/load-samples", response_model=BatchOut)
def load_samples():
    """Convenience for demos: ingest the 10 Climb sample tickets."""
    items = json.loads((DATA / "sample_tickets.json").read_text())
    tickets = [TicketIn(text=i["text"], source="climb-samples", external_id=str(i["id"])) for i in items]
    decisions = _process_many(tickets)
    return BatchOut(count=len(decisions), decisions=decisions)


@app.get("/tickets", response_model=list[Decision])
def list_tickets(limit: int = 100, queue: str | None = None):
    return audit.list_recent(limit=limit, queue=queue)


@app.get("/tickets/{decision_id}", response_model=Decision)
def get_ticket(decision_id: str):
    d = audit.get(decision_id)
    if not d:
        raise HTTPException(404, "unknown ticket id")
    return d


@app.get("/tickets/{decision_id}/explain", response_class=PlainTextResponse)
def explain(decision_id: str):
    d = audit.get(decision_id)
    if not d:
        raise HTTPException(404, "unknown ticket id")
    x = d.extraction
    lines = [
        f"Ticket {d.id}  ({d.created_at}, mode={d.mode}, model={d.model or '-'})",
        "",
        f"  Customer:   {x.customer.name or 'unknown'}  ids={x.customer.identifiers or '-'}",
        f"  Category:   {x.category.value} (confidence {x.category_confidence:.2f})",
        f"  Urgency:    {x.urgency.value}  signals={x.urgency_signals or '-'}",
        f"  Escalate:   {x.escalate}  reasons={[r.value for r in x.escalation_reasons] or '-'}",
        f"  Routed to:  {d.queue}" + (f"  + {d.escalation_queue}" if d.escalation_queue else ""),
        "",
        "Model rationale:",
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


@app.get("/queues")
def queues():
    counts = audit.queue_counts()
    return {"total": audit.total(), "queues": [{"name": q, "count": counts.get(q, 0)} for q in routing.all_queues()]}


@app.delete("/tickets")
def clear_all():
    audit.clear()
    return {"ok": True}
