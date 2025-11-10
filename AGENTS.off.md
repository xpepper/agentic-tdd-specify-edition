# AGENTS.md

See @PROJECT.md for full project description.

Purpose: Guidance for agentic contributors building multi-agent TDD prototype.
Keep the README.md and PROJECT.md updated with project status and goals.

### Development Environment
Build/Setup: run `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`.
Install deps via pyproject; avoid global installs.
Tests: run all `pytest -q`; single test `pytest tests/test_fib.py::test_fib0 -q`.
Re-run last failing: `pytest --lf -q`.
Lint/Format: use `ruff check .` then `ruff format .`; fix incrementally.
Type checking: `mypy src`.

### Committing
Pre-commit: ensure `pytest -q` green, `ruff check .` clean (or staged fixes), `ruff format .` applied, and `mypy src` passes before committing.
Keep commits focused; avoid unrelated formatting; include AGENTS.md compliance in PR summary.
Use Conventional Commits (`feat:`, `refactor:`, `test:`, `fix:`, `doc:`, `chore:`) for messages.
