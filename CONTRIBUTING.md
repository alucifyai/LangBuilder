# Contributing

Thanks for your interest in contributing! This document provides a short checklist to help contributors get started and make effective contributions.

## Getting your environment ready

1. Install system prerequisites:
   - Python 3.10–3.13
   - Node.js and npm
   - pipx (recommended)

2. Install project dependencies and developer tooling:

```bash
make init
```

This runs backend and frontend dependency installation and sets up pre-commit hooks.

## Code style and quality

- Format Python with `ruff` and the configured rules: `make format` (calls formatters for both backend and frontend).
- Linting and type checks: `make lint` (runs mypy and other checks).
- Run `make help` to see other Makefile targets.

## Running tests

- Unit tests (Python backend): `make unit_tests`
- Frontend tests (Jest / Playwright): use `make test_frontend` or `make tests_frontend` for e2e

If your change adds behavior, include unit tests and ensure tests pass locally before opening a PR.

## Making a PR

1. Create a feature branch from `main`.
2. Make small, focused commits with clear messages.
3. Run formatters and linters locally.
4. Run the test suite relevant to your change.
5. Open a PR with a descriptive title, summary, and testing notes.

## Reviewing

Reviewers will check for:
- Correctness and tests
- Clear commit history
- No sensitive data or secrets in the code

Thanks — we appreciate your contribution!
