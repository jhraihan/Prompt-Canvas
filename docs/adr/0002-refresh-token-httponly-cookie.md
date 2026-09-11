# 2. Refresh token is an httpOnly, rotated cookie

**Status:** Accepted · **Date:** 2026-09-09 (inherited, documented here)

## Context

The refresh token is the long-lived credential — fourteen days here. If it is
readable by script, ADR 0001 buys nothing: an attacker takes the refresh token
instead and mints access tokens at will.

## Decision

The refresh token is never in a response body. It is set as a cookie that is:

- `httpOnly`, so no script on any origin can read it;
- `Secure` and `SameSite=None`, forced by cross-origin hosting (see ADR 0003);
- scoped to `path=/api/auth/`, so it is not attached to image requests;
- **rotated on every use**, with the previous token blacklisted.

## Consequences

- A stolen refresh token is single-use at best: the moment the legitimate
  client refreshes, the stolen copy is blacklisted, and vice versa. Replay is
  detectable rather than silent.
- The blacklist grows; a weekly `flushexpiredtokens` cron trims it.
- `SameSite=None` means the cookie rides along on cross-site requests, so CSRF
  needs a separate answer — ADR 0003.
- Completing a password reset blacklists every outstanding token for the
  account, which is what actually evicts an attacker who already has one.
