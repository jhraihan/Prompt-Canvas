# 7. Local tooling, not containers

**Status:** Accepted · **Date:** 2026-09-10

## Context

"Clone and `docker compose up`" is the conventional answer to onboarding, and
it removes "install PostgreSQL" from the setup instructions.

## Decision

No `Dockerfile`, no `docker-compose.yml`. Python 3.12+, Node 20+, and
PostgreSQL 14+ installed on the host are the supported path, wrapped in a
`Makefile`.

## Consequences

- **Accepted:** a newcomer installs PostgreSQL once. The README says so plainly
  rather than implying a one-command setup that does not exist.
- **Avoided:** a second definition of the runtime that drifts from the real one,
  and a container layer between a developer and the process they are debugging.
- The backend suite needs none of it: 251 tests run on SQLite against the stub
  provider, so the only prerequisite for testing is Python and a
  `DJANGO_SECRET_KEY`. PostgreSQL is required to run the dev server with real
  data, not to contribute.
- Deployment is unaffected — the VPS runs gunicorn under systemd either way.
