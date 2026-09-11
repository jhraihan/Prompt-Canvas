# Changelog

All notable changes to this project are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **A marketing landing page** at `/` for signed-out visitors: gradient display
  headline, drifting colour wash, floating stat pills, colour-coded feature
  cards, and a three-step explainer. Signed-in users skip it and land on the
  generator.
- **A motion layer** in `global.css` -- aurora drift, float, staggered reveal,
  gradient pan, hover lift. Everything animates only `transform` and `opacity`
  so it composites on the GPU, and all of it is decorative: the interface works
  identically with `prefers-reduced-motion` set.
- **A shared demo account.** With `VITE_DEMO_EMAIL` and `VITE_DEMO_PASSWORD`
  set, the sign-in screen offers one-click access. The account is forced to be
  non-staff and non-superuser on every run of `create_demo_user`, since those
  credentials ship in the public bundle.
- **OpenAPI schema and Swagger UI** at `/api/schema/` and `/api/docs/`,
  generated from the serializers so the documentation cannot drift from the
  code. All 23 endpoints are documented; the plain `APIView`s carry explicit
  request/response annotations because nothing could infer them.
- **Structured JSON logging with request correlation.** Every line carries an
  `X-Request-ID`, taken from an inbound header when a proxy supplies one and
  echoed back on the response, so a user can quote it in a bug report. An
  inbound id is length-capped and sanitised: it is written into log output, so
  a newline in it would let a caller forge a log line.
- **Optional error tracking (Sentry).** A complete no-op without `SENTRY_DSN`.
  When enabled, `send_default_pii` is off and a scrubber strips headers,
  cookies, and password fields — the defaults would otherwise ship prompts, the
  `Authorization` header, and the refresh cookie to a third party.
- **End-to-end tests.** 9 Playwright specs driving a real browser against a
  real server: register, generate, history, delete, session restore, ownership
  isolation, saved prompts, and anonymous share-link access. Runs on SQLite
  against the stub provider, so no database service and no provider token.
- **Architecture decision records** in `docs/adr/` — seven, covering the token
  strategy, the CSRF defence, the provider abstraction, the quality mapping,
  and both deferrals (no async queue, no containers).
- **Saved prompts.** Keep a prompt with the size and quality it was used at,
  and restore the whole setup in one click. Saved prompts are stored separately
  from generations, so deleting an image never discards the wording.
- **Bulk delete.** Selection mode in the history gallery with select-all and a
  single confirmation. Ids belonging to another account are silently skipped
  rather than reported, so the endpoint confirms nothing about what exists.
- **Visible generation quota.** Read from the same throttle cache DRF enforces,
  so the figure shown is the figure applied — there is no second counter to
  drift. Returned with every generation and from `/api/images/quota/`.
- **Model picker.** A curated `MODEL_CATALOGUE` exposed through the options
  endpoint. The request field is a ChoiceField against that allowlist: without
  it, a client could point the server's provider credential at any model on the
  hub.
- **Expiring share links.** Opt-in, revocable links to a single generation,
  with a public read-only page. This addresses the limitation recorded in
  SECURITY.md: a media file URL cannot expire or be revoked, so a share link is
  the thing the owner actually controls. Revoked, expired, and never-existed
  all return an identical 404.
- **Password reset by email.** Request a link, redeem it, and the new password
  takes effect. The request endpoint answers identically whether or not the
  address has an account, so it cannot be used to discover who is registered —
  including when SMTP itself fails. Tokens are single-use: the current password
  hash is part of the signed payload, so completing a reset invalidates every
  outstanding link for that account. A reset also blacklists every existing
  refresh token, evicting an attacker who already had a session.
- **Email verification.** Sent on registration and resendable. Deliberately
  soft: an unverified account signs in and generates normally, and sees a
  dismissible banner explaining that without a confirmed address there is no
  way to recover the account.
- SMTP configuration through environment variables, with the console backend in
  development so the reset link prints to the terminal and no mail account is
  needed to test the flow.
- Separate rate-limit budgets for login, registration, and the token endpoints
  (`LOGIN_RATE`, `REGISTER_RATE`, `TOKEN_RATE`). Previously login and
  registration shared one `anon` bucket, so sign-up traffic spent the same
  allowance meant to slow password guessing.
- Rate limiting on `/api/auth/refresh/` and `/api/auth/logout/`, which were
  unauthenticated POST endpoints performing a database write with no cap.
- `/api/health/` now reports the active `provider`, `model`, and a `degraded`
  flag, so a misconfigured provider is visible to a monitor rather than only in
  the log.
- Django system check `images.E001`, which fails the deploy if the stub
  provider is configured in production. The stub returns placeholder gradients
  and never errors, so without this a misconfigured deployment looks completely
  healthy while every image is meaningless.
- `ruff` for backend linting and formatting, gated in CI. The backend
  previously had no linter at all.
- Coverage floor of 90% enforced in CI.
- `pip-audit` and `npm audit` as blocking CI steps.
- Dependabot for pip, npm, and GitHub Actions.
- Pre-commit hooks: ruff, formatting, large-file and private-key detection, and
  a provider-token scan.
- `Makefile` wrapping setup, test, lint, format, and run tasks.
- `.editorconfig`, `CONTRIBUTING.md`, `SECURITY.md`, and this changelog.
- `docs/PRD.md` — requirements, defect register, and roadmap.

### Changed

- **Rebuilt the palette around a warm amber accent.** Dark is the default -- a
  brown-black ground rather than the previous neutral near-black -- with light
  as a full peer theme on cream. Four decorative secondaries were added for the
  landing page.
- Migrated email configuration to Django 6.1's `MAILERS` setting. The flat
  `EMAIL_*` settings are deprecated and removed in Django 7.0, and defining
  both raises an error.
- **Renamed the project from Chitra AI to Prompt Canvas** across 54 files.
  Identifiers were mapped by context: CSS custom properties `--chitra-*` →
  `--pc-*`, the systemd unit → `promptcanvas-api`, the database →
  `promptcanvas`, the site user → `prompt-canvas`, the logging namespace →
  `promptcanvas.*`, and the refresh cookie → `pc_refresh`.
- Default branch is `main`, not `master`.
- Deployment is fully parameterised. `deploy/bootstrap.sh` requires
  `API_DOMAIN` and `APP_ORIGIN` from the environment and validates them;
  `deploy/deploy.sh` reads its identity from `~/.deploy-env`;
  `deploy/cloudpanel-vhost.conf` is a template rendered at bootstrap. Nothing
  about a specific host is committed.
- CI reads the deployment origins from repository variables rather than
  literals.
- Backend test coverage raised from 86% to 93%; the Hugging Face provider from
  57% to 98%, and `create_demo_user` from 0% to 100%.
- `media_root` moved to a root `conftest.py` so no test in any app can write
  into the real `MEDIA_ROOT`.

### Fixed

- Dead CSS selector `:root[data-theme="system"]:where(.light-preferred)`. The
  class was never applied anywhere, and `ThemeProvider` never sets
  `data-theme="system"` — it removes the attribute — so the rule could not
  match. `tokens.test.js` now fails if such a selector reappears.
- `--pc-accent-fg` was defined in the explicit light-theme block but missing
  from the `prefers-color-scheme: light` block. Latent (both values were
  `#ffffff`), but the two blocks must stay identical; a test now enforces that.
- `HistoryPage` no longer depends on a context callback inside its mount
  effect, which was correct only while `notify` stayed referentially stable.
- Corrected stale references: `demo.ts` → `demo.js`, `deploy/nginx.conf` →
  `deploy/cloudpanel-vhost.conf`, and the frontend test count in the README.
- README setup used `.venv/bin/` paths throughout, which do not exist on
  Windows.
- **The header's Generate and History links had no accessible name below the
  `sm` breakpoint.** Their labels sit in a `hidden sm:inline` span, which is
  `display:none` on a narrow viewport, leaving the links unlabelled for a
  screen reader. Found by the end-to-end suite, whose default viewport is
  narrow enough to expose it; every unit test rendered wide enough to miss it.
- `renderWithProviders` put a route's query string inside `pathname`, where a
  "?" is a literal path character — so `useSearchParams` saw nothing and no
  test could cover a link-driven page.
- The CI secret-scan comment claimed the `.env.example` placeholder was too
  short to match the token pattern. It is not — the scan passes because
  template files are excluded by path.

### Security

- Removed a committed `.claude/settings.json` containing a root SSH invocation
  that exposed a production server's IP address. `.claude/` is now gitignored.
- Removed an inherited incident log documenting another operator's
  infrastructure and unrotated credentials.

## [1.0.0] — inherited baseline

The starting point: a working full-stack image generator with a provider
abstraction, JWT cookie authentication, private per-user history, and a
complete design system. 82 backend and 72 frontend tests passing.

[Unreleased]: https://github.com/YOUR_USER/prompt-canvas/compare/v1.0.0...HEAD
