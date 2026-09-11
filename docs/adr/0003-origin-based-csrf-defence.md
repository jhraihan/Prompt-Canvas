# 3. CSRF defence by `Origin` validation

**Status:** Accepted · **Date:** 2026-09-09 (inherited, documented here)

## Context

The SPA is on Vercel and the API is on a VPS: different origins. That forces
`SameSite=None` on the refresh cookie (ADR 0002) — without it the browser would
not send the cookie at all.

`SameSite` is normally the defence against CSRF. Setting it to `None` removes
that defence entirely: any page on the internet can POST to
`/api/auth/refresh/` and the browser will attach the cookie.

Django's CSRF middleware does not help here — it protects session-authenticated
form posts, not a cookie read by a DRF view.

## Decision

`TrustedOrigin` (`accounts/security.py`) validates the `Origin` header against
`CORS_ALLOWED_ORIGINS` on every state-changing, cookie-authenticated request.
A browser stamps `Origin` from the page's own origin and will not let script
forge it, so an attacker page fails the check.

Requests presenting neither `Origin` nor `Referer` are allowed through.

## Consequences

- The browser threat model is covered: a cross-site POST from an attacker page
  carries that page's `Origin` and is rejected with 403.
- **The no-header fallback is the known gap.** A non-browser client — curl, a
  script, anything not stamping `Origin` — passes. This keeps server-to-server
  calls and the test client working, and is recorded as a limitation in
  `SECURITY.md`. It matters only to an attacker who already holds the cookie,
  which requires a compromise this control was never going to stop.
- Adding a frontend origin means updating `CORS_ALLOWED_ORIGINS`; forgetting to
  is a 403, not a silent failure.

## Alternatives considered

- **A custom header the SPA always sets** (`X-Requested-With`). Simple browsers
  cannot forge it cross-origin either, and it closes the no-header gap. Not
  adopted because it breaks non-browser clients with no threat-model gain.
- **Double-submit cookie.** More moving parts for the same guarantee.
