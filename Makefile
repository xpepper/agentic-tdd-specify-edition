.PHONY: help install fmt lint test clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies with Poetry"
	@echo "  make fmt      - Format code with black"
	@echo "  make lint     - Lint code with ruff and mypy"
	@echo "  make test     - Run tests with pytest"
	@echo "  make clean    - Remove build artifacts and cache"

install:
	poetry install

fmt:
	poetry run black agentic_tdd tests
	poetry run ruff check --fix agentic_tdd tests

lint:
	poetry run ruff check agentic_tdd tests
	poetry run mypy agentic_tdd

test:
	poetry run pytest

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
