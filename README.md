# LangBuilder (langflow)

A developer-focused repository for LangFlow — a Python web application and frontend GUI for building language workflows.

This repository includes the backend (Python) and frontend (React) sources, developer tooling and Makefile commands to build, run and test the project.

## Quick start

- Install system requirements: Python 3.10–3.13, Node.js & npm, and pipx (optional).
- Run the project init which installs backend and frontend dependencies:

```bash
make init
```

To run backend only (development):

```bash
make backend
```

To run frontend only (development):

```bash
make frontend
```

To build frontend static files and copy them for packaging:

```bash
make build_frontend
```

To run unit tests:

```bash
make unit_tests
```

For a full list of available developer commands, run:

```bash
make help
```

## Project layout

- `src/backend` — Backend Python application and packages
- `src/frontend` — Frontend React application
- `src/backend/base` — Langflow base package and build targets
- `docs` — Docusaurus website sources
- `Makefile` / `Makefile.frontend` — Developer commands used throughout the docs below

## Packaging & publishing

The project uses `uv` and `hatchling` for packaging and dependency management. See `pyproject.toml` for package metadata and dependencies. Typical workflow:

```bash
# lock dependencies and build
uv lock
uv build
# install locally
pip install dist/*.whl
```

## Further documentation

See `CONTRIBUTING.md`, `RUNNING.md`, and `TESTS.md` for more detailed developer instructions.