# 6. Generation stays synchronous

**Status:** Accepted · **Date:** 2026-09-10

## Context

A generation takes roughly eight seconds and holds a gunicorn worker for the
whole time. With three workers, a handful of concurrent generations saturates
the server.

The standard answer is Celery plus Redis: the request returns immediately with
a job id and the client polls. It also enables progress reporting and retries.

## Decision

Stay synchronous. Do not add Celery or Redis.

## Consequences

- **Accepted:** throughput is capped at roughly three concurrent generations.
  At the scale this project runs — a portfolio deployment with a per-user rate
  limit of 20 generations an hour — that ceiling is never reached.
- **Avoided:** a broker to install, keep running, monitor, and secure; a worker
  process and its systemd unit; a poll-for-status flow through the frontend;
  and a whole class of failure modes (lost jobs, stuck queues, worker drift)
  that only pay for themselves under load that does not exist.
- gunicorn's `--timeout 180` and nginx's `proxy_read_timeout` must stay well
  above the slowest cold generation. Both have ample headroom.
- Revisit if real traffic arrives. Nothing in the current design blocks it: the
  service layer is already a single function that a task could wrap.
