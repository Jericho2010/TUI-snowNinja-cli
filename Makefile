.PHONY: install test lint format run clean

SHELL := /bin/bash

install:
	@echo "Installing SnowNinja..."
	chmod +x setup.sh && ./setup.sh

test:
	@echo "Running tests..."
	uv run pytest tests/unit tests/e2e -v

lint:
	@echo "Linting with Ruff..."
	uv run ruff check .
	@echo "Checking formatting with Ruff..."
	uv run ruff format --check .

format:
	@echo "Formatting with Ruff..."
	uv run ruff format .
	uv run ruff check --fix .

run:
	@echo "Launching SnowNinja..."
	./run.sh

clean:
	@echo "Cleaning up..."
	rm -rf .venv .pytest_cache .ruff_cache dist build
	find . -type d -name "__pycache__" -exec rm -rf {} +
