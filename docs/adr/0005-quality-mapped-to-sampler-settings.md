# 5. Quality tiers map to sampler settings

**Status:** Accepted · **Date:** 2026-09-09 (inherited, documented here)

## Context

The product offers "Standard" and "High detail". FLUX has no quality parameter,
so the tier has to mean something concrete or it means nothing.

The naive mapping — more steps is better — is wrong per model.
FLUX.1-schnell is timestep-distilled: it converges in about four steps and
ignores classifier-free guidance. Running it at 40 steps with guidance 7 costs
ten times as much and produces a worse image.

## Decision

`QUALITY_PROFILES` in `images/constants.py` maps each tier to real sampler
settings **per model family**:

| Family | Standard | High detail |
|---|---|---|
| schnell | 4 steps, guidance 0.0 | 8 steps, guidance 0.0 |
| dev | 20 steps, guidance 3.5 | 40 steps, guidance 4.5 |
| anything else | 25 steps, guidance 7.0 | 45 steps, guidance 7.5 |

`quality_profile(model, quality)` returns a copy, so a caller cannot mutate the
table.

## Consequences

- The tiers mean something on every model, including ones added later, which
  fall into the `default` family rather than getting schnell's settings.
- A new model family is a dictionary entry, not a code change.
- Tests assert that high detail always costs more steps than standard, and that
  schnell keeps guidance at zero.
