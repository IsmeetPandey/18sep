"""Small SQLite persistence layer with explicit transactions and constraints."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  author TEXT NOT NULL,
  body TEXT NOT NULL,
  reach INTEGER NOT NULL DEFAULT 0 CHECK (reach >= 0),
  intent TEXT NOT NULL,
  priority TEXT NOT NULL,
  score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
  status TEXT NOT NULL,
  sla_deadline TEXT NOT NULL,
  assignee TEXT,
  response_draft TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(provider, provider_event_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interaction_id INTEGER NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL,
  detail TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interactions_status_priority ON interactions(status, priority);
CREATE INDEX IF NOT EXISTS idx_interactions_deadline ON interactions(sla_deadline);
CREATE INDEX IF NOT EXISTS idx_audit_interaction ON audit_events(interaction_id, created_at);
"""


@contextmanager
def connect(path: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: str) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
