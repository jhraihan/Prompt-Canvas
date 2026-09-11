# Prompt Canvas — Product Requirements Document

**Status:** Active
**Owner:** hello.jahidhr@gmail.com
**Created:** 2026-09-09
**Last updated:** 2026-09-10
**Version:** 2.5
**Owner name:** Md. Jahid Hasan Raihan

---

## 1. Product

Prompt Canvas turns a natural-language prompt into an image, and keeps every
generation in a private, searchable history the author can return to, download,
or regenerate.

The concept is inherited from a prior codebase; this document defines the
product **going forward**. The starting codebase is treated as a reference
implementation, not as content to preserve. Where the existing approach is
sound it is kept; where it is weak it is replaced.

### 1.1 Principles

1. **The image is the product.** Every interface decision serves showing the
   generated image and getting out of its way.
2. **The credential never leaves the server.** The provider token is server-side
   only, in every environment, without exception.
3. **A failure explains itself.** Users get a plain-language cause and a way
   forward. Diagnostics stay in the log.
4. **Provider-agnostic by construction.** Adding an image provider is one
   subclass and one registry entry — no view, serializer, or model change.
5. **Nothing about a host lives in the repository.** Domains, IPs, and users are
   supplied by the environment, so the same tree deploys anywhere.

### 1.2 Stack

| Layer | Choice |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router |
| Backend | Django 6, Django REST Framework, SimpleJWT |
| Database | PostgreSQL |
| Provider | Hugging Face Inference Providers (FLUX.1-schnell default) |
| Storage | Filesystem behind a swappable interface |
| Hosting | Vercel (frontend), VPS + CloudPanel (backend) |
| CI/CD | GitHub Actions |

---

## 2. Current state

Measured 2026-09-10, not estimated.

| Check | Result |
|---|---|
| Backend tests | 251 passed (was 82) |
| Frontend tests | 107 passed (was 72) |
| Backend coverage | 94.7% (was 86%) — CI floor at 90% |
| End-to-end tests | 9 passed, real browser against a real server |
| Migration drift | None |
| Backend lint/format | ruff clean (was: no linter at all) |
| Frontend lint | 0 errors, 5 warnings (was 6) |
| Production build | 277 kB raw / 86.6 kB gzipped |

### 2.1 What already works well

These are load-bearing and stay:

- **Provider and storage abstractions.** Clean ABCs with a registry; the stub
  provider makes the whole suite runnable offline with no token.
- **Token strategy.** Access token in memory only; refresh token in an httpOnly,
  path-scoped, rotated cookie with blacklist-on-rotation. Parallel 401s collapse
  into one refresh.
- **Error translation.** Every provider failure becomes a domain error carrying
  a fixed user-safe message; response bodies and tokens are never logged or
  returned.
- **Ownership isolation.** Every queryset is filtered by `request.user`; another
  account's image is a 404, not a 403.
- **Quality mapping.** FLUX has no quality parameter, so tiers map to real
  sampler settings per model family.

---

## 3. Ownership reset — COMPLETE

The project was cloned from an upstream repository. This section records what
was removed so the work is auditable.

### 3.1 Contributor history

`.git` was absent from the clone, so no upstream history, authorship, or
contributor record existed in the tree. A fresh `git init` yields a repository
whose sole contributor is the owner. **No history rewriting was needed.**

### 3.2 Infrastructure purge — done

| Action | Result |
|---|---|
| Deleted `.claude/settings.json` | Removed a committed root SSH invocation exposing the previous server IP |
| Deleted `docs/PROD_PROVIDER_FIX.md` | Inherited incident log narrating another operator's debugging session on their host |
| Parameterized `deploy/bootstrap.sh` | `API_DOMAIN` / `APP_ORIGIN` now required from the environment, validated, no defaults |
| Parameterized `deploy/deploy.sh` | Reads identity from `~/.deploy-env`, written by bootstrap; no literals |
| Templated `deploy/cloudpanel-vhost.conf` | `__API_DOMAIN__` / `__APP_ORIGIN__` / `__SITE_USER__` / `__PORT__`, rendered by bootstrap |
| Rewrote `docs/DEPLOYMENT.md` | Owner-specific record → generic placeholder-driven guide |
| Moved origins to GitHub **variables** | `vars.API_ORIGIN` / `vars.APP_ORIGIN` replace hardcoded `env:` literals |
| Renamed default branch | `master` → `main` across workflows and docs |
| Added `.gitignore` rules | `.claude/` and generated `docs/*.pdf` |

**Verified:** a search for the previous domains, IP, and VM identifier across
`docs`, `deploy`, `.github`, `README.md`, `backend`, and `frontend/src` returns
**zero matches**. Both deploy scripts pass `bash -n`; both workflows parse as
valid YAML; the three bootstrap validation guards were exercised and fail fast
with actionable messages; the vhost template renders with no placeholders left.

### 3.3 Remaining owner action

| Item | Why |
|---|---|
| **Rotate the Hugging Face token** | The inherited token existed in at least two `.env` files and is documented in a chat transcript. Treat as compromised; issue a new one. |
| **Provision new infrastructure** | New VPS/domains; the previous host's credentials were noted as exposed. Nothing in this tree references them any more. |

---

## 4. Defect register

Severity: **P1** fix before launch · **P2** quality · **P3** polish

Kept as a record of what was found and what was done about it. Status as of
2026-09-10: every P1 is fixed; SEC-3 and SEC-4 remain open by decision.

| ID | Sev | Defect | Status |
|---|---|---|---|
| **SEC-1** | **P1** | Login and register share one throttle bucket (`throttle_scope = "anon"`), so `ANON_RATE=30/hour` is a *combined* budget. 30 password attempts/hour is loose, and registration consumes the same allowance. | **FIXED** (R1.1) |
| **SEC-2** | **P1** | No throttle on `RefreshView` or `LogoutView`. Both are unauthenticated POST endpoints; refresh performs a DB write on every call. | **FIXED** (R1.2) |
| **SEC-3** | **P2** | The Origin guard allows requests presenting neither `Origin` nor `Referer`. Verified: such a POST to `/api/auth/refresh/` returns **200** and rotates the cookie. Deliberate and sound against browsers, but the one CSRF control resting on an assumption rather than a check. | **OPEN** — needs a decision, see §8.3 |
| **SEC-4** | **P2** | No per-account lockout. Rate limiting is per-IP only, so a distributed attempt against one account is unthrottled. | **OPEN** — deferred to R1.4 |
| **SEC-5** | **P2** | No dependency vulnerability scanning. The CI security job greps for tokens but never audits dependencies. | **FIXED** (R2.5) |
| **BUG-1** | **P2** | Dead CSS selector. `.light-preferred` appears exactly once in the codebase — in the selector requiring it — and nothing adds the class. Verified at runtime that `data-theme` is only ever `"light"`, `"dark"`, or absent, never `"system"`, so the rule can never match. | **FIXED** (R1.5) |
| **BUG-2** | **P2** | `--pc-accent-fg` is defined in the `[data-theme="light"]` block (27 tokens) but missing from the `prefers-color-scheme: light` block (26). Latent — both values are `#ffffff` today — but the blocks must stay identical. | **FIXED** (R1.5) |
| **BUG-3** | **P2** | `set-state-in-effect`: `load` is a `useCallback` depending on `notify`, called from a `useEffect` depending on `load`. Works only because `notify` is stable; a change there creates a fetch loop. | **FIXED** (R1.6) — residual warning is a linter false positive |
| **ENG-1** | **P1** | No Python linter or formatter — no `ruff`, `black`, `flake8`, or `pyproject.toml`. The frontend gates `oxlint` in CI; the backend has no equivalent. | **FIXED** (R1.7) |
| **ENG-2** | **P1** | `HuggingFaceProvider` is 57% covered — the lowest in the codebase. `_translate_http_error` is well tested, but `generate()` (network call, PIL encode, six exception branches) is never exercised. | **FIXED** (R1.8) — now 98% |
| **ENG-3** | **P2** | No coverage floor in CI. `pytest-cov` is installed but never invoked or enforced. | **FIXED** (R2.1) — floor at 90% |
| **ENG-4** | **P2** | `create_demo_user` is 0% covered (32 statements) despite writing user records and resetting passwords. | **FIXED** (R2.2) — now 100% |
| **PROV-1** | **P1** | **A misconfigured provider fails silently.** If `IMAGE_PROVIDER=stub` reaches production, users get gradients with no signal anywhere. This is the single highest-value operational fix. | **FIXED** (R1.9) |

### 4.2 Found by the end-to-end suite

| ID | Sev | Defect | Status |
|---|---|---|---|
| **A11Y-1** | **P2** | The header's Generate and History links label themselves with a `hidden sm:inline` span. Below the `sm` breakpoint that span is `display:none`, so **the links had no accessible name at all** — a screen reader on a narrow viewport announced them as unlabelled. Found because Playwright's default viewport is below `sm` and could not resolve the link by name. | **FIXED** — explicit `aria-label` on both. |

This is the class of defect unit tests cannot reach: every existing test
rendered at a viewport where the label was visible.

### 4.1 Fixed already

| Fix | Detail |
|---|---|
| Stale `demo.ts` reference | Corrected to `demo.js` in `create_demo_user.py` |
| Stale `deploy/nginx.conf` reference | Corrected to `cloudpanel-vhost.conf` in `config/urls.py` |
| README test count | `63` → `72` frontend tests |
| README branch | `master` → `main` |

---

## 5. Requirements

### 5.1 Phase 1 — Correctness & security — COMPLETE

| Req | Requirement | Acceptance |
|---|---|---|
| R1.1 | Split `login` and `register` throttle scopes; add `LOGIN_RATE` (default `10/hour`). | **DONE** — `login` + `register` scopes added; 5 tests incl. the regression that login exhaustion no longer blocks registration |
| R1.2 | Throttle `RefreshView` and `LogoutView`. | **DONE** — `token` scope on refresh + logout, tested |
| R1.3 | Resolve SEC-3 explicitly: keep with a documented rationale, or require an SPA-only custom header. | Decision recorded as an ADR; behaviour matches. |
| R1.4 | Per-account lockout with progressive backoff. | N failures against one account lock it regardless of source IP. |
| R1.5 | Fix BUG-1 and BUG-2; add a test asserting both light-theme blocks define an identical token set. | **DONE** — dead selector removed, `--pc-accent-fg` added; `tokens.test.js` asserts both blocks stay in sync (verified it fails when the bug is reintroduced) |
| R1.6 | Fix BUG-3. | **DONE** — restructured; the residual oxlint warning is a false positive (verified: the minimal correct pattern is flagged identically) and is suppressed with a documented reason |
| R1.7 | Adopt `ruff` (lint + format); add `pyproject.toml`; gate in CI. | **DONE** — ruff adopted, `pyproject.toml` added, gated in CI; 43 findings triaged to zero |
| R1.8 | Cover `HuggingFaceProvider.generate()` with a mocked client — success and all six exception branches. | **DONE** — 19 tests with a mocked client; coverage 57% → 98% |
| **R1.9** | **Make provider misconfiguration loud.** Report `provider` and `model` from `/api/health/`; make `check --deploy` fail when `IMAGE_PROVIDER=stub` under production settings. | A stub-in-prod deploy is blocked, not silently shipped. |
| R1.10 | Add `LICENSE`. | **DEFERRED** by owner decision. Without one the repo is all-rights-reserved: nobody may legally use or run it. Revisit before publishing. |

### 5.2 Phase 2 — Engineering practice — COMPLETE

| Req | Requirement | Acceptance |
|---|---|---|
| R2.1 | Enforce a coverage floor in CI. | **DONE** — floor raised to 90% as coverage reached 93.4%. |
| R2.2 | Test `create_demo_user`. | **DONE** — 15 tests; coverage 0% → 100%. Includes the privilege-demotion tests: an existing superuser is stripped of rights, since the credentials ship publicly. |
| R2.3 | Add `.pre-commit-config.yaml`: ruff, ruff-format, trailing whitespace, large files, private-key detection. | **DONE** — `.pre-commit-config.yaml` with ruff, formatting, large-file/private-key detection, and a token scan. Underlying checks verified clean. |
| R2.4 | Add `.github/dependabot.yml` for pip, npm, and actions. | **DONE** — pip, npm, and github-actions, with grouped patch updates. |
| R2.5 | Add `pip-audit` and `npm audit --audit-level=high` to CI. | **DONE** — both audits added and verified passing (0 vulnerabilities each). |
| ~~R2.6~~ | ~~Add `Dockerfile` + `docker-compose.yml`.~~ | **DROPPED** by owner decision. Local Python + Node + PostgreSQL is the single supported path. Criterion 4 (a stranger runs the stack from a clean checkout) is met instead by `make setup` and an accurate README. |
| R2.7 | Add a `Makefile` wrapping setup, test, lint, format, run. | **DONE** — `make help` lists 20 targets; venv path resolves on both Windows and POSIX. |
| R2.8 | Add `.editorconfig`. | **DONE** — aligned with ruff (90 cols, 4-space Python) and the frontend's 2-space convention. |
| R2.9 | Add `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`. | **DONE** — all four added. `SECURITY.md` documents the controls *and* the known limitations. |
| R2.10 | Add PR and issue templates. | **DONE** — PR template plus bug/feature issue forms; blank issues disabled, security routed to SECURITY.md. |

### 5.3 Phase 3 — Product features — COMPLETE except the deferred queue

Ordered by value. R3.1 is not optional in the way the rest are.

| Req | Feature | Rationale |
|---|---|---|
| **R3.1** | **Password reset via email.** | **DONE** — request/confirm endpoints, single-use tokens, session eviction on reset, three SPA screens. 30 backend + 15 frontend tests. |
| R3.2 | Email verification on registration. | **DONE** — soft verification per owner decision: unverified accounts work normally and see a dismissible banner. Sent on registration; resend endpoint provided. |
| ~~R3.3~~ | ~~Async generation queue (Celery + Redis).~~ | **DEFERRED** by owner decision. Adds Redis as a service to install and keep running, for a throughput problem that does not exist at this scale (3 gunicorn workers, ~8s generations). Revisit when real traffic justifies the operational cost. |
| R3.4 | Prompt history and favourites. | **DONE** — saved prompts with settings, lazy-loaded panel, use counter. A saved prompt outlives the images made from it. |
| R3.5 | Bulk actions in history (multi-select delete/download). | **DONE** — selection mode, select-all, one confirmation. Foreign ids are silently skipped rather than reported, so the endpoint confirms nothing about another account. |
| R3.6 | Visible usage quota. | **DONE** — read from the same throttle cache DRF enforces, so the number shown is the number enforced. Returned with each generation and from `/api/images/quota/`. |
| R3.7 | Image-to-image / variations. | **DEFERRED** — the provider abstraction supports it, but it needs its own UI (source image upload, strength control). Not started. |
| R3.8 | Model picker from a curated list. | **DONE** — curated allowlist in `MODEL_CATALOGUE`; a ChoiceField rejects anything unlisted, so a client cannot point the server credential at an arbitrary model. |
| R3.9 | Opt-in expiring share links. | **DONE** — expiring, revocable share links with a public read-only page. Directly addresses the SEC-7 limitation. |
| R3.10 | Admin analytics: volume, error rates, latency percentiles. | **DEFERRED** — admin analytics. Not started. |

### 5.4 Phase 4 — Observability & polish — COMPLETE

| Req | Requirement | Acceptance |
|---|---|---|
| R4.1 | `drf-spectacular`; serve OpenAPI + Swagger UI. | **DONE** — `drf-spectacular`; all 23 paths documented with zero generator errors. Swagger at `/api/docs/`, schema at `/api/schema/`. |
| R4.2 | Structured JSON logging with a request-ID middleware. | **DONE** — JSON logs with an `X-Request-ID` correlation id, echoed to the caller. An inbound id is sanitised: it lands in log output, so a newline in it would forge a log line. |
| R4.3 | Error tracking (Sentry), off by default, enabled by env var. | **DONE** — Sentry, no-op without `SENTRY_DSN`. `send_default_pii` off plus a scrubber, because the default would ship prompts, the Authorization header, and the refresh cookie to a third party. |
| R4.4 | Playwright E2E: register → generate → history → download → delete. | **DONE** — 9 Playwright tests through a real browser. Found a genuine accessibility defect (see §4.2). |
| R4.5 | README badges: CI, license, coverage. | **DONE** — CI, coverage, test-count, and version badges. No license badge, since none is chosen. |
| R4.6 | ADRs for decisions already made — in-memory access token, httpOnly refresh cookie, Origin-based CSRF defence, provider/storage abstraction, quality mapping. | **DONE** — 7 ADRs in `docs/adr/`, including the two deferrals so the trade-offs are on record. |

---

## 6. Deployment

Infrastructure is provisioned fresh under the owner's control. Nothing in the
repository names a host.

### 6.1 Configuration surface

| Source | Carries |
|---|---|
| `backend/.env` (gitignored) | Secret key, `DATABASE_URL`, `HF_TOKEN`, origins, rate limits |
| `~/.deploy-env` (on the VPS, written by bootstrap) | `DOMAIN`, `SITE_USER`, `GUNICORN_PORT`, `GIT_BRANCH` |
| GitHub **variables** | `API_ORIGIN`, `APP_ORIGIN`, `DEPLOY_SCRIPT_PATH` |
| GitHub **secrets** | `VPS_HOST`, `VPS_USER`, `VPS_PORT`, `VPS_SSH_KEY`, `VPS_HOST_KEY`, `VERCEL_*` |
| Vercel env | `VITE_API_BASE_URL`, optional `VITE_DEMO_*` |

Origins are **variables, not secrets**: they are public (the API origin is
compiled into the client bundle regardless), and masking them would break the
CI step that greps built assets to verify the origin was baked in.

### 6.2 Bootstrap contract

`deploy/bootstrap.sh` requires `API_DOMAIN` and `APP_ORIGIN`, validates that
`APP_ORIGIN` carries a scheme, and refuses to run otherwise. It is idempotent
and never overwrites an existing `.env`.

### 6.3 Open decision

Keep the CloudPanel VPS, or move to a PaaS (Railway, Fly.io, Render)? The VPS
gives full control and cheap image storage; a PaaS is reproducible by a stranger
in minutes and removes the bootstrap script entirely. **Recommendation:** keep
the VPS — the deploy tooling is already written and tested, and filesystem media
storage is a genuine cost advantage.

---

## 7. Success criteria

1. `git shortlog -sne` lists exactly one contributor.
2. No credential, IP, or inherited domain anywhere in the tree. **Met.**
3. CI gates tests, lint, format, coverage floor, and dependency audit — all blocking.
4. A stranger runs the stack from a clean checkout by following the README:
   install Python 3.12+, Node 20+, and PostgreSQL 14+, then `make setup`.
   Backend tests need none of it beyond Python — they run on SQLite against the
   stub provider, so no database server and no provider token are required.
5. `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` present and accurate.
6. Backend coverage ≥ 85%, no module below 80%.
7. A misconfigured provider cannot reach production silently.
8. Users can recover a forgotten password. **Met.**
9. Every path, command, and number in the docs resolves.

---

## 8. Open questions

1. **License** — MIT or Apache-2.0? MIT is the common default for portfolio work;
   Apache-2.0 adds an explicit patent grant.
2. **Async queue (R3.3)** — in scope now, or after launch? It is the largest
   single change proposed and adds Redis as a dependency.
3. **SEC-3** — keep the documented open fallback, or require an SPA-only header?
4. **Email provider for R3.1/R3.2** — transactional service (Resend, Postmark,
   SES) or SMTP?
5. **Repository visibility** — public or private? Public makes Phase 2's
   community files matter immediately.
