# Prompt Canvas — development tasks.
#
# Requires Python 3.12+, Node 20+, and PostgreSQL 14+ on the host. There is no
# container path: local tooling is the single supported way to run this project.
#
#   make setup     one-time: virtualenv, dependencies, .env files
#   make dev       run both servers (two terminals; see `make help`)
#   make test      everything CI runs
#
# Windows note: these targets assume a POSIX shell (Git Bash, WSL, or macOS or
# Linux). The venv's binaries live in Scripts/ on Windows and bin/ elsewhere,
# which VENV_BIN below resolves automatically.

SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND  := backend
FRONTEND := frontend
VENV     := $(BACKEND)/.venv

# Windows puts console scripts in Scripts/, POSIX in bin/.
VENV_BIN := $(shell [ -d "$(VENV)/Scripts" ] && echo "$(VENV)/Scripts" || echo "$(VENV)/bin")
PY       := ../$(VENV_BIN)/python

.PHONY: help setup setup-backend setup-frontend env dev dev-backend dev-frontend \
        test test-backend test-frontend cov lint format check migrate \
        superuser demo-user provider-check build clean

help: ## Show this help
	@echo "Prompt Canvas"
	@echo ""
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Two servers are needed for local work. In separate terminals:"
	@echo "  make dev-backend     API on http://localhost:8000"
	@echo "  make dev-frontend    app on http://localhost:5173"

# --- Setup -----------------------------------------------------------------

setup: setup-backend setup-frontend env ## One-time setup: venv, deps, .env files
	@echo ""
	@echo "Setup complete. Next:"
	@echo "  1. Create the database:  createdb promptcanvas"
	@echo "  2. Edit backend/.env — set DATABASE_URL and DJANGO_SECRET_KEY"
	@echo "     (generate a key with: make secret)"
	@echo "  3. make migrate"
	@echo "  4. make dev-backend  /  make dev-frontend"
	@echo ""
	@echo "No Hugging Face token? Leave IMAGE_PROVIDER=stub — the whole app"
	@echo "works offline against a local placeholder generator."

setup-backend: ## Create the virtualenv and install Python dependencies
	@test -d $(VENV) || python -m venv $(VENV)
	@cd $(BACKEND) && $(PY) -m pip install --upgrade pip --quiet
	@cd $(BACKEND) && $(PY) -m pip install -r requirements-dev.txt --quiet
	@echo "backend dependencies installed"

setup-frontend: ## Install Node dependencies
	@cd $(FRONTEND) && npm ci
	@echo "frontend dependencies installed"

env: ## Create .env files from the examples (never overwrites)
	@if [ ! -f $(BACKEND)/.env ]; then \
	  cp $(BACKEND)/.env.example $(BACKEND)/.env; \
	  echo "created $(BACKEND)/.env — edit it before running"; \
	else echo "$(BACKEND)/.env exists, left untouched"; fi
	@if [ ! -f $(FRONTEND)/.env ]; then \
	  cp $(FRONTEND)/.env.example $(FRONTEND)/.env; \
	  echo "created $(FRONTEND)/.env"; \
	else echo "$(FRONTEND)/.env exists, left untouched"; fi

secret: ## Print a fresh DJANGO_SECRET_KEY
	@cd $(BACKEND) && $(PY) -c \
	  "from django.core.management.utils import get_random_secret_key as k; print(k())"

# --- Run -------------------------------------------------------------------

dev-backend: ## Run the Django API on :8000
	@cd $(BACKEND) && $(PY) manage.py runserver

dev-frontend: ## Run the Vite dev server on :5173
	@cd $(FRONTEND) && npm run dev

# --- Test ------------------------------------------------------------------

test: test-backend test-frontend ## Run every test (what CI runs)

test-backend: ## Backend tests (SQLite + stub provider; no database server needed)
	@cd $(BACKEND) && $(PY) -m pytest

test-frontend: ## Frontend tests
	@cd $(FRONTEND) && npm test

test-e2e: ## End-to-end tests in a real browser (starts both servers)
	@cd $(FRONTEND) && npm run test:e2e

schema: ## Write the OpenAPI schema to backend/schema.yml
	@cd $(BACKEND) && $(PY) manage.py spectacular --file schema.yml
	@echo "wrote $(BACKEND)/schema.yml"

cov: ## Backend tests with the CI coverage floor
	@cd $(BACKEND) && $(PY) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=90

# --- Quality ---------------------------------------------------------------

lint: ## Lint both sides
	@cd $(BACKEND) && $(PY) -m ruff check .
	@cd $(FRONTEND) && npm run lint

format: ## Auto-format and apply safe lint fixes
	@cd $(BACKEND) && $(PY) -m ruff check . --fix
	@cd $(BACKEND) && $(PY) -m ruff format .

check: ## Everything CI enforces, in CI's order
	@cd $(BACKEND) && $(PY) -m ruff check .
	@cd $(BACKEND) && $(PY) -m ruff format --check .
	@cd $(BACKEND) && $(PY) manage.py makemigrations --check --dry-run
	@$(MAKE) cov
	@cd $(FRONTEND) && npm run lint && npm test && npm run build

# --- Django ----------------------------------------------------------------

migrate: ## Apply database migrations
	@cd $(BACKEND) && $(PY) manage.py migrate

superuser: ## Create an admin account
	@cd $(BACKEND) && $(PY) manage.py createsuperuser

demo-user: ## Create or reset the shared demo account
	@cd $(BACKEND) && $(PY) manage.py create_demo_user \
	  --email $${EMAIL:?set EMAIL=...} --password $${PASSWORD:?set PASSWORD=...}

provider-check: ## Smoke-test the configured image provider (never prints the token)
	@cd $(BACKEND) && $(PY) manage.py check_provider

build: ## Production frontend build
	@cd $(FRONTEND) && npm run build

clean: ## Remove build artifacts and caches
	@rm -rf $(FRONTEND)/dist $(FRONTEND)/coverage
	@rm -rf $(FRONTEND)/test-results $(FRONTEND)/playwright-report
	@rm -f $(BACKEND)/e2e.sqlite3 $(BACKEND)/schema.yml
	@rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.ruff_cache $(BACKEND)/htmlcov
	@rm -f $(BACKEND)/.coverage
	@find $(BACKEND) -type d -name __pycache__ -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned"
