# 4. Providers and storage behind narrow interfaces

**Status:** Accepted · **Date:** 2026-09-09 (inherited, documented here)

## Context

The product generates images through Hugging Face and writes them to local
disk. Both are the kind of choice that changes: a provider gets expensive, a
model is retired, disk becomes the wrong place once there is more than one box.

Calling the SDK directly from a view is faster to write and welds the
application to one vendor.

## Decision

Two abstract base classes, each with a registry keyed by an environment
variable:

- `ImageProvider` — `generate()` and `describe()`. Selected by `IMAGE_PROVIDER`.
- `ImageStorage` — `save()`, `delete()`, `url_for()`. Selected by `IMAGE_STORAGE`.

Nothing above the service layer knows Hugging Face exists. Views and models see
a key and a URL.

## Consequences

- Adding a provider is one subclass and one registry entry. Adding S3 or R2 is
  the same for storage.
- `StubProvider` paints a deterministic gradient, which is why the whole suite
  runs offline with no token, and why a contributor can work on any part of the
  app without a Hugging Face account.
- The stub is also a hazard: it never errors, so a deployment left on it looks
  healthy while serving placeholders. That is what `images.E001` and the
  `degraded` flag on `/api/health/` exist to catch.
- Every provider failure must be translated into a `GenerationError` at this
  boundary. Letting an SDK exception escape would leak response bodies that can
  echo the prompt or the `Authorization` header.
