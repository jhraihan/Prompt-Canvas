## What this changes

<!-- One or two sentences. What is different after this merges? -->

## Why

<!-- The problem, not the solution. Link an issue if there is one. -->

## How to verify

<!-- The steps a reviewer takes to see it working. Be specific:
     which page, which command, what they should observe. -->

## Checklist

- [ ] `make check` passes locally (lint, format, migrations, coverage floor, frontend build)
- [ ] Tests added or updated — a bug fix includes the test that would have caught it
- [ ] No secret, domain, IP address, or hostname added to the tree
- [ ] `CHANGELOG.md` updated under `[Unreleased]` if this is user-visible
- [ ] Documentation updated if behaviour, setup, or the API changed

## If this touches auth, storage, or the provider layer

<!-- Delete this section if it does not. -->

- [ ] I have read the relevant section of `SECURITY.md`
- [ ] No provider response body, header, or token can reach a response or a log
- [ ] What I considered and rejected:

## User-visible impact

<!-- What will someone using the app notice? "None" is a valid answer. -->
