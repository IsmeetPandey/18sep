# SignalDesk

**Social engagement triage and response operations for small teams.**

SignalDesk turns a stream of social comments and direct-message events into an accountable workflow: normalize incoming interactions, classify intent, prioritize risk and revenue signals, assign ownership, track SLA state, and keep an audit trail for every decision.

## Why it exists

Social teams often have the tools to publish content but still manage the work that follows in fragmented inboxes. The operational failure is not a missing scheduler; it is losing important conversations among routine engagement. Current workflow guidance emphasizes structured engagement, triage, assignment, follow-up, and measurable outcomes. citeturn0search10turn0search3

## Core workflow

`ingest → deduplicate → classify → prioritize → assign → respond/resolve → audit → measure`

The MVP is deliberately integration-agnostic. It accepts normalized events through an API, so real platform adapters can be added later without coupling domain logic to one provider.

## Capabilities

- Idempotent ingestion using provider event IDs.
- Rule-based intent classification for questions, complaints, leads, praise, and spam.
- Explainable priority scoring based on intent, sentiment signal, reach, and age.
- SLA deadlines and overdue detection.
- Explicit assignment and lifecycle states (`open`, `in_progress`, `resolved`, `ignored`).
- Response drafts stored separately from the original interaction.
- Append-only audit events for operational traceability.
- Bounded pagination and strict input validation.
- SQLite persistence with foreign-key enforcement.
- API-key protection for write operations when `SIGNALDESK_API_KEY` is configured.
- Health endpoint and deterministic CI checks.

## Architecture

FastAPI HTTP layer → Pydantic validation → domain services → SQLite repository.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the data model, state transitions, scoring model, and extension boundaries.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `SIGNALDESK_API_KEY` to require `X-API-Key` on write endpoints. Without the variable, local development remains frictionless.

## Verification

```bash
ruff check .
mypy app
python -m compileall -q app tests
pytest -q
```

## Non-goals

SignalDesk is not an autonomous social account operator, accounting system, CRM replacement, or platform-specific scraper. It does not publish replies without an explicit downstream integration and approval policy.

## Security

See [`SECURITY.md`](SECURITY.md). The design assumes untrusted external events, duplicate delivery, malformed payloads, and abusive request volume.

## License

MIT
