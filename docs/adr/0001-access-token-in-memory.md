# 1. Access token lives in JavaScript memory only

**Status:** Accepted · **Date:** 2026-09-09 (inherited, documented here)

## Context

The SPA needs an access token on every API call. The obvious homes are
`localStorage`, `sessionStorage`, or a JavaScript variable.

`localStorage` is the common choice and the worst one: any script running on
the page can read it. A single XSS — in the app, or in any dependency it pulls
— hands an attacker a token that keeps working until it expires, from any
machine.

## Decision

The access token is held in a module-level variable in `frontend/src/lib/api.js`
and written nowhere else. A page reload discards it; the client then calls
`/api/auth/refresh/` and the browser supplies the refresh cookie.

## Consequences

- An XSS payload finds nothing on disk. It can still make requests *while it is
  running on the page*, but it cannot exfiltrate a token for later use.
- Every cold load costs one refresh round trip before the app is usable. This
  is why `ProtectedRoute` shows a spinner rather than the sign-in screen: the
  session is unknown, not absent.
- Multiple tabs each hold their own copy. Parallel 401s collapse into one
  refresh so they do not race.
- A test asserting the token is absent from both storages guards this
  (`api.test.js`).
