# Contributing to Prompt Canvas

## Setting up

**Requires** Python 3.12+, Node 20+, and PostgreSQL 14+. There is no container
path — local tooling is the supported way to run this project.

```bash
make setup          # virtualenv, dependencies, .env files
createdb promptcanvas
make migrate
```

Then, in two terminals:

```bash
make dev-backend    # API on :8000
make dev-frontend   # app on :5173
```

`make help` lists every task. Without GNU Make, the README has the same steps
by hand.

> On Windows a virtualenv puts its executables in `.venv/Scripts/`, not
> `.venv/bin/`. The Makefile detects this; the README's manual commands need
> substituting.

**You do not need a Hugging Face token.** Leave `IMAGE_PROVIDER=stub` and the
whole application works offline against a local generator that paints a
deterministic gradient. Validation, storage, history, download, and delete all
behave identically.

**You do not need PostgreSQL to run the tests.** The suite runs on SQLite
against the stub provider, in a temporary media directory. A `backend/.env`
with `DJANGO_SECRET_KEY` set is the only prerequisite.

## Before you commit

```bash
pre-commit install    # once per clone
```

That wires the hooks in `.pre-commit-config.yaml`: ruff, formatting, trailing
whitespace, large-file and private-key detection, and a provider-token scan.
They catch what CI catches, minutes earlier.

To run the full gate yourself:

```bash
make check
```

which is exactly what CI runs: ruff lint, ruff format check, a
missing-migration check, the test suite with a 90% coverage floor, then the
frontend lint, tests, and production build.

Never use `git commit --no-verify` to get past a real failure.

## Standards

**Tests are not optional.** The coverage floor in CI is a ratchet: raise it
when coverage rises, never lower it to make a red build pass. A bug fix should
come with the test that would have caught it.

**Comments explain why, not what.** The code already says what it does. A
comment earns its place by recording a decision, a constraint, or a trap — the
reason a line is written the way it is rather than the obvious way.

**Match the surrounding code.** Naming, structure, and comment density should
be indistinguishable from the file you are editing.

**Nothing host-specific in the repository.** Domains, IP addresses, usernames,
and ports come from the environment. A checkout must be portable to any host.

**Secrets never enter the tree.** `.env` is gitignored; `.env.example` holds
placeholders only. If you commit a credential, rotate it — git history keeps it
forever, so a revert is not a fix.

## Architecture worth knowing

**Adding an image provider** is one subclass of `ImageProvider` plus one
registry entry in `images/services/providers/__init__.py`. Nothing above the
service layer knows Hugging Face exists. Storage works the same way via
`ImageStorage`.

**Provider failures must never leak.** Every upstream error is translated into
a `GenerationError` subclass carrying a fixed, user-safe `user_message`.
Response bodies, headers, and tokens are never returned and never logged — they
can echo the prompt or the `Authorization` header.

**Token handling is deliberate.** The access token lives in a module-level
variable in the API client and is never written to storage. The refresh token
is an httpOnly cookie scoped to `/api/auth/`. See `SECURITY.md` before changing
either.

**The design system is the contract.** No component may hard-code a colour,
radius, shadow, duration, or type size — every one is a token in
`frontend/src/styles/tokens.css`. The light theme is defined twice (explicit
choice and OS preference) and `tokens.test.js` fails if the two drift.

## Pull requests

Keep them focused: one concern per PR. A branch that fixes a bug and reformats
four unrelated files is hard to review and harder to revert.

Fill in the template. If a change is user-visible, say what a user will notice.
If it touches auth, storage, or the provider layer, say what you considered and
rejected.

Green CI is required. It is not advisory.
