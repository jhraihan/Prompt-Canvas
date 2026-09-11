# Security Policy

## Reporting a vulnerability

Email **hello.jahidhr@gmail.com** with the subject line `SECURITY: Prompt Canvas`.

Please do not open a public issue for a security problem. A public report is
visible to everyone, including anyone who would exploit it, before there is a
fix.

Include what you have: the affected endpoint or file, what an attacker can do
with it, and the steps to reproduce. A proof of concept helps but is not
required — a clear description of the flaw is enough to start.

You can expect an acknowledgement within a few days. This is a personal
project, not a funded programme: there is no bounty, and fixes land as quickly
as one maintainer can manage.

## Supported versions

The `main` branch is the only supported version. Fixes land there; there are no
backported release branches.

## What this project already does

Reporting is more useful when you know what is deliberate. The following are
design decisions, not oversights:

| Control | Where |
|---|---|
| Provider token is server-side only, never in a response or a log | `images/services/providers/huggingface.py` |
| Access token held in JavaScript memory only, never `localStorage` | `frontend/src/lib/api.js` |
| Refresh token in an httpOnly, `Secure`, path-scoped cookie, rotated and blacklisted on every use | `accounts/views.py`, `accounts/security.py` |
| `Origin` validated on cookie-authenticated endpoints (CSRF defence, since `SameSite=None` is forced by cross-origin hosting) | `accounts/security.py` |
| Separate rate-limit budgets for login, registration, and token endpoints | `config/settings/base.py` |
| Every queryset filtered by `request.user`; another account's image is a 404, not a 403 | `images/views.py` |
| Provider errors translated to fixed user-safe messages; diagnostics stay in the log | `config/exception_handler.py`, `images/exceptions.py` |
| HTTPS, HSTS, and secure cookies enforced | `config/settings/prod.py` |
| CI blocks a committed provider token or a tracked `.env` | `.github/workflows/ci.yml` |
| CI audits dependencies (`pip-audit`, `npm audit`) | `.github/workflows/ci.yml` |
| Password reset cannot be used to discover which addresses have accounts | `accounts/views.py` |
| Reset tokens are single-use and evict every existing session | `accounts/tokens.py`, `accounts/views.py` |
| The model field is an allowlist, so the provider credential cannot be aimed at an arbitrary model | `images/constants.py` |
| Share links expire, are revocable, and a dead one is indistinguishable from one that never existed | `images/models.py`, `images/views.py` |
| A misconfigured provider fails the deploy rather than silently serving placeholders | `images/checks.py` |

## Known limitations

These are understood trade-offs, documented so a report can focus on something
new. They are still worth raising if you can show impact beyond what is
described.

**Media URLs are unguessable, not access-controlled.** A generated image lives
at a path containing a random 32-hex key. Anyone holding the URL can fetch it
without authenticating — the URL *is* the capability. Directory listing is off,
so keys cannot be enumerated, but a leaked file URL grants permanent access and
cannot be revoked.

Share links exist because of this: a share link expires, can be revoked, and is
the only sharing mechanism the owner actually controls. The share UI says so
explicitly rather than letting someone assume the file URL behaves the same
way. Signed, expiring media URLs remain the fuller fix if this project ever
holds genuinely sensitive images.

**The `Origin` guard allows requests carrying neither `Origin` nor `Referer`.**
Browsers always attach `Origin` to cross-site POSTs, so this does not weaken
the browser threat model, and it keeps server-to-server and CLI clients
working. It does mean a non-browser client holding a stolen refresh cookie is
not stopped by this particular control.

**Rate limiting is per-IP.** A distributed attempt against a single account is
not throttled per-account. Per-account lockout is planned (PRD R1.4).

**The demo account is deliberately public.** When `VITE_DEMO_EMAIL` and
`VITE_DEMO_PASSWORD` are set, those credentials ship in the client bundle. The
account is forced to be non-staff and non-superuser on every run of
`create_demo_user`, and its history is visible to every visitor by design.
