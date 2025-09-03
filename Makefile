.PHONY: help test lint format security check install clean pre-commit-install pre-commit-run

help:
	@echo "Available targets:"
	@echo "  install    Install dependencies"
	@echo "  test       Run pytest tests"
	@echo "  lint       Run ruff linter"
	@echo "  format     Format code with ruff"
	@echo "  security   Run bandit security checks"
	@echo "  check      Run all checks (lint, format, security, test)"
	@echo "  clean      Clean cache files"
	@echo "  pre-commit-install  Install pre-commit hooks"
	@echo "  pre-commit-run      Run pre-commit on all files"

install:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install ruff bandit pre-commit

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

test:
	pytest -v

lint:
	ruff check --fix --ignore E722 .

format:
	ruff format .

security:
	bandit -r . -x ./test_*.py

check: lint security test
	@echo "All checks passed!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
