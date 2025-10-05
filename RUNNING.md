# Running the project (developer guide)

This file explains the common commands to run the backend and frontend during development and how to build the frontend for packaging.

## Environment

- Default backend host: `0.0.0.0`, port: `7860` (see `Makefile` variables).
- Environment file: the Makefile uses `env ?= .env` by default. Create a `.env` at repo root to configure keys and settings required by the app.

## Run backend (development)

Install backend deps and run:

```bash
make install_backend
make backend
```

This starts the Python backend (uvicorn) on the configured port. If you need auto-login or different ports, set `login`, `host` and `port` variables when calling `make`.

Examples:

```bash
# run on port 8000
make backend port=8000

# run with auto login
make backend login=true
```

## Run frontend (development)

Install frontend deps and start the dev server:

```bash
make install_frontend
make frontend
```

This runs the React development server on port 3000 by default.

## Build frontend static files

To build the production frontend and copy assets into the backend package:

```bash
make build_frontend
```

After a successful build the compiled frontend will be copied to `src/backend/base/langflow/frontend` and included when packaging.

## Running the packaged app

After building and installing the package locally:

```bash
uv build
pip install dist/*.whl
uv run langflow run --frontend-path src/backend/base/langflow/frontend
```

Or simply use the provided Makefile wrapper:

```bash
make run_cli
```

## Docker

There are Docker targets in the `Makefile` to build images and run docker-compose for examples in `docker_example`.

```bash
make docker_build
make docker_compose_up
```
