# SignalDesk architecture

## Boundary

SignalDesk owns the workflow after a normalized social interaction reaches the system. Platform-specific ingestion belongs in adapters outside the core domain. This prevents vendor APIs from leaking into classification, SLA, and lifecycle rules.

## Data model

- **Interaction** — immutable provider identity plus normalized content, triage result, SLA deadline, assignment, response draft, lifecycle timestamps.
- **AuditEvent** — append-only operational history linked to an interaction.

A unique `(provider, provider_event_id)` constraint makes ingestion idempotent. Foreign keys are enabled on every SQLite connection.

## Triage

Classification is deterministic and explainable. Commercial intent and complaints receive higher scores; spam indicators reduce score; reach and aging can raise urgency. The resulting priority maps to a response SLA. The score is a workflow signal, not a claim about customer value.

## State machine

`open ↔ in_progress → resolved`

`open → ignored → open`

Terminal `resolved` interactions cannot be reopened accidentally. Every transition is audited.

## API

- `GET /health`
- `POST /interactions`
- `GET /interactions?status=&priority=&limit=&offset=`
- `PATCH /interactions/{id}/status`
- `PATCH /interactions/{id}/assignment`
- `PATCH /interactions/{id}/draft`
- `GET /interactions/{id}/audit`

Write endpoints can require `X-API-Key` when `SIGNALDESK_API_KEY` is configured. Authentication is intentionally small for this repository; production deployments should put the API behind a managed identity layer and enforce tenant-level authorization.

## Trade-offs

SQLite keeps local development deterministic and avoids an unnecessary service dependency. The repository layer is deliberately thin so it can be replaced with PostgreSQL without moving domain rules. Rule-based triage is preferred to an opaque model because the first operational requirement is explainability; an optional classifier can be introduced behind the same domain contract later.

## Scaling path

A production deployment can add an event queue for ingestion, provider adapters, Postgres, tenant-scoped authorization, durable job workers, rate limiting at the edge, metrics/tracing, and encrypted managed storage. Those are extension points, not simulated features in the MVP.
