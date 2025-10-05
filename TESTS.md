# Tests

This project includes Python unit and integration tests (pytest) for the backend and Jest/Playwright tests for the frontend. Use the Makefile targets below.

## Backend (Python)

- Run unit tests:

```bash
make unit_tests
```

- Run integration tests:

```bash
make integration_tests
```

- Run all tests and coverage report:

```bash
make tests
```

Notes:
- The `pyproject.toml` configures pytest options and default testpaths `src/backend/tests`.
- Tests that require API keys are marked with the `api_key_required` marker. Use `-m "not api_key_required"` to skip them (the Makefile does this by default for unit tests).

## Frontend

- Install frontend deps and run unit tests (Jest):

```bash
make install_frontend
make test_frontend
```

- Run Playwright e2e tests (Chromium):

```bash
make tests_frontend
```

## Coverage

- The `coverage` target in the Makefile runs pytest with coverage and produces an HTML report under `coverage/`.

## CI tips

- Keep test times reasonable. The Makefile supports splitting and parallel pytest runs; CI may set `-n auto` via the Makefile.
- Ensure to run formatters and linters in CI (`make format` and `make lint`).
