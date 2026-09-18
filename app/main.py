"""SignalDesk HTTP API."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
import sqlite3
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .db import connect, init_db
from .domain import deadline, triage, validate_transition
from .models import AssignmentIn, AuditOut, DraftIn, InteractionIn, InteractionOut, StatusIn

DB_PATH = os.getenv("SIGNALDESK_DB", "signaldesk.db")
API_KEY = os.getenv("SIGNALDESK_API_KEY")
MAX_LIMIT = 100
app = FastAPI(title="SignalDesk", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db(DB_PATH)


def require_write_access(x_api_key: str | None = Header(default=None)) -> None:
    if API_KEY is not None and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")


def now() -> datetime:
    return datetime.now(timezone.utc)


def row_to_interaction(row: sqlite3.Row) -> InteractionOut:
    return InteractionOut(
        id=row["id"], provider=row["provider"], provider_event_id=row["provider_event_id"],
        author=row["author"], body=row["body"], reach=row["reach"], intent=row["intent"],
        priority=row["priority"], score=row["score"], status=row["status"],
        sla_deadline=datetime.fromisoformat(row["sla_deadline"]), assignee=row["assignee"],
        response_draft=row["response_draft"], created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def audit(conn: sqlite3.Connection, interaction_id: int, event_type: str, actor: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO audit_events(interaction_id,event_type,actor,detail,created_at) VALUES(?,?,?,?,?)",
        (interaction_id, event_type, actor, detail, now().isoformat()),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/interactions", response_model=InteractionOut, status_code=201, dependencies=[Depends(require_write_access)])
def ingest(payload: InteractionIn) -> InteractionOut:
    current = now()
    result = triage(payload.body, payload.reach)
    with connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT * FROM interactions WHERE provider=? AND provider_event_id=?",
            (payload.provider, payload.provider_event_id),
        ).fetchone()
        if existing:
            return row_to_interaction(existing)
        cursor = conn.execute(
            """INSERT INTO interactions
            (provider,provider_event_id,author,body,reach,intent,priority,score,status,sla_deadline,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (payload.provider, payload.provider_event_id, payload.author, payload.body, payload.reach,
             result.intent, result.priority, result.score, "open", deadline(result.sla_minutes, current).isoformat(),
             current.isoformat(), current.isoformat()),
        )
        interaction_id = int(cursor.lastrowid)
        audit(conn, interaction_id, "ingested", "system", "; ".join(result.reasons) or "default triage")
        row = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        assert row is not None
        return row_to_interaction(row)


@app.get("/interactions", response_model=list[InteractionOut])
def list_interactions(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[InteractionOut]:
    clauses: list[str] = []
    args: list[Any] = []
    if status:
        clauses.append("status=?")
        args.append(status)
    if priority:
        clauses.append("priority=?")
        args.append(priority)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            f"SELECT * FROM interactions{where} ORDER BY score DESC, created_at DESC LIMIT ? OFFSET ?",
            (*args, limit, offset),
        ).fetchall()
        return [row_to_interaction(row) for row in rows]


@app.patch("/interactions/{interaction_id}/status", response_model=InteractionOut, dependencies=[Depends(require_write_access)])
def set_status(interaction_id: int, payload: StatusIn, x_actor: str | None = Header(default=None)) -> InteractionOut:
    with connect(DB_PATH) as conn:
        row = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="interaction not found")
        try:
            validate_transition(row["status"], payload.status)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        timestamp = now().isoformat()
        conn.execute("UPDATE interactions SET status=?, updated_at=? WHERE id=?", (payload.status, timestamp, interaction_id))
        audit(conn, interaction_id, "status_changed", x_actor or "api", f"{row['status']} -> {payload.status}")
        updated = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        assert updated is not None
        return row_to_interaction(updated)


@app.patch("/interactions/{interaction_id}/assignment", response_model=InteractionOut, dependencies=[Depends(require_write_access)])
def assign(interaction_id: int, payload: AssignmentIn, x_actor: str | None = Header(default=None)) -> InteractionOut:
    with connect(DB_PATH) as conn:
        row = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="interaction not found")
        conn.execute("UPDATE interactions SET assignee=?, updated_at=? WHERE id=?", (payload.assignee, now().isoformat(), interaction_id))
        audit(conn, interaction_id, "assigned", x_actor or "api", payload.assignee or "unassigned")
        updated = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        assert updated is not None
        return row_to_interaction(updated)


@app.patch("/interactions/{interaction_id}/draft", response_model=InteractionOut, dependencies=[Depends(require_write_access)])
def save_draft(interaction_id: int, payload: DraftIn, x_actor: str | None = Header(default=None)) -> InteractionOut:
    with connect(DB_PATH) as conn:
        row = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="interaction not found")
        conn.execute("UPDATE interactions SET response_draft=?, updated_at=? WHERE id=?", (payload.draft, now().isoformat(), interaction_id))
        audit(conn, interaction_id, "draft_saved", x_actor or "api", "response draft updated")
        updated = conn.execute("SELECT * FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        assert updated is not None
        return row_to_interaction(updated)


@app.get("/interactions/{interaction_id}/audit", response_model=list[AuditOut])
def get_audit(interaction_id: int, limit: int = Query(default=100, ge=1, le=MAX_LIMIT)) -> list[AuditOut]:
    with connect(DB_PATH) as conn:
        exists = conn.execute("SELECT 1 FROM interactions WHERE id=?", (interaction_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="interaction not found")
        rows = conn.execute(
            "SELECT event_type,actor,detail,created_at FROM audit_events WHERE interaction_id=? ORDER BY id DESC LIMIT ?",
            (interaction_id, limit),
        ).fetchall()
        return [AuditOut(**dict(row), created_at=datetime.fromisoformat(row["created_at"])) for row in rows]


def event_fingerprint(provider: str, event_id: str) -> str:
    """Stable identifier useful to adapters that need a compact key."""
    return hashlib.sha256(f"{provider}:{event_id}".encode()).hexdigest()
