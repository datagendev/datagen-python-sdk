# Repository Guidelines

## Project Structure & Module Organization
- `datagen_sdk/`: Core SDK. `client.py` exposes `DatagenClient.execute_tool`, handling auth, retries, and Datagen API responses; `__init__.py` re-exports public classes.
- `examples/`: Small runnable samples (`list_projects.py`, `list_issues.py`) showing tool execution against a local MCP service.
- `pyproject.toml`: Package metadata and build config (setuptools); `requirements.txt`: runtime deps (requests); `README.md`: user-facing quick start.

## Setup, Build & Run
- Create a virtual env and install in editable mode: `python -m venv .venv && source .venv/bin/activate && pip install -e .`.
- Set credentials: export `DATAGEN_API_KEY="<key>"`; override API host with `DatagenClient(base_url="http://localhost:3001")` or env var before running examples.
- Run examples locally: `python examples/list_projects.py` or `python examples/list_issues.py`; they should print fetched items when the MCP backend is reachable.

## Testing Guidelines
- No automated tests yet; add `tests/` with `test_*.py` using `pytest` (recommended) and run via `pytest` from repo root.
- Prefer unit coverage around HTTP error handling, retry/backoff, and auth failures; mock outbound `requests.post` calls to avoid live network coupling.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, lowercase_with_underscores for functions/variables, CapWords for classes.
- Type hints are expected for public APIs; raise `DatagenError` subclasses for predictable failures.
- Use f-strings for formatting, keep imports standard-library | third-party | local, separated by blank lines.
- Keep user-facing messages concise; default base URL remains `http://localhost:3001` unless explicitly overridden.

## Commit & Pull Request Guidelines
- Commits: present-tense, imperative, short (e.g., `Add retry backoff`, `Fix auth error path`). Squash fixups before review when possible.
- PRs: include scope/intent, test evidence (`pytest` output if added), and note any API changes or new env vars. Link related issues; add a short demo snippet when behavior changes (e.g., sample `DatagenClient` call).

## Security & Configuration Tips
- Never commit API keys; rely on `DATAGEN_API_KEY` env variable or secrets manager. Avoid printing full responses that may contain sensitive data.
- When adding new tools, validate response shape and guard against missing fields before accessing nested keys to prevent leaking traceback details.

## Architecture Snapshot
- SDK centers on `DatagenClient.execute_tool`, which POSTs to `/api/tools/execute` with `tool_alias_name` and `parameters`. Responses are expected as `{success, data: {success, result}}`; failures raise typed exceptions (`DatagenAuthError`, `DatagenToolError`, `DatagenHttpError`).
- Keep the public surface minimal; prefer helper functions in separate modules under `datagen_sdk/` rather than expanding `client.py` monolithically.
