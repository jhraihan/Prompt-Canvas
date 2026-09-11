# Architecture Decision Records

Short records of decisions that are expensive to reverse or easy to
misread as arbitrary. Each states the forces at the time, what was chosen, and
what it costs — so a future reader can tell a deliberate trade-off from an
accident.

Written after the fact for decisions inherited or made during the 2026-09
hardening work; new ones are written as the decision is taken.

| # | Decision | Status |
|---|---|---|
| [0001](0001-access-token-in-memory.md) | Access token lives in JavaScript memory only | Accepted |
| [0002](0002-refresh-token-httponly-cookie.md) | Refresh token is an httpOnly, rotated cookie | Accepted |
| [0003](0003-origin-based-csrf-defence.md) | CSRF defence by `Origin` validation | Accepted |
| [0004](0004-provider-and-storage-abstraction.md) | Providers and storage behind narrow interfaces | Accepted |
| [0005](0005-quality-mapped-to-sampler-settings.md) | Quality tiers map to sampler settings | Accepted |
| [0006](0006-no-async-queue.md) | Generation stays synchronous | Accepted |
| [0007](0007-local-tooling-not-containers.md) | Local tooling, not containers | Accepted |

## Format

Context → Decision → Consequences. Short enough to read in a minute. A record
is never edited once accepted: it is superseded by a new one that links back.
