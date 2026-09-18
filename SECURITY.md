# Security

## Threat boundaries

SignalDesk treats provider payloads, authors, message text, and provider event IDs as untrusted input. The API does not fetch URLs from interaction content, execute user-supplied code, or deserialize arbitrary objects.

### Controls

- Pydantic bounds input sizes and formats.
- SQLite queries use parameters; dynamic SQL is limited to a fixed allowlisted filter shape.
- Provider event IDs are unique to make retries idempotent.
- Write endpoints support an API key through an environment variable; secrets are never stored in the repository.
- SQLite foreign keys and transactions preserve referential integrity.
- Pagination is bounded to prevent unbounded result responses.
- The application does not send social replies automatically.

## Production recommendations

Use TLS at the edge, managed identity/tenant authorization, a secrets manager, request rate limits, structured redacted logging, encrypted managed storage, dependency scanning, and provider webhook signature verification before accepting internet traffic.

## Reporting

Do not open a public issue for a suspected security vulnerability. Report it privately to the repository owner through GitHub's supported private security-reporting mechanism when enabled, or contact the maintainer through the account's current contact channel.
