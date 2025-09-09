.PHONY: help test lint format security check install clean lefthook-install lefthook-run

help:
	@echo "Available targets:"
	@echo "  install    Install dependencies"
	@echo "  test       Run pytest tests"
	@echo "  lint       Run ruff linter"
	@echo "  format     Format code with ruff"
	@echo "  security   Run bandit security checks"
	@echo "  check      Run all checks (lint, format, security, test)"
	@echo "  clean      Clean cache files"
	@echo "  lefthook-install    Install lefthook git hooks"
	@echo "  lefthook-run        Run lefthook pre-commit hooks"

install:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install ruff bandit lefthook

lefthook-install:
	lefthook install

lefthook-run:
	lefthook run pre-commit

test:
	pytest tests/ -v

lint:
	ruff check --fix --ignore E722 src/ tests/
	find . -name "*.yml" -o -name "*.yaml" |xargs -t yamllint -c .yamllint.yaml

format:
	ruff format src/ tests/

security:
	bandit -r src/

check: lint security test
	@echo "All checks passed!"

clean:
	find src/ tests/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find src/ tests/ -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .ruff_cache
