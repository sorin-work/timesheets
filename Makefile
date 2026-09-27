# Shortcuts for local development. Run `make help` for the list.

API := api
WEB := web
PY := $(API)/.venv/bin

.PHONY: help install dev-api dev-web test test-api test-web lint format up down

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## install api and web dependencies
	python3.12 -m venv $(API)/.venv
	$(PY)/pip install -r $(API)/requirements-dev.txt
	cd $(WEB) && npm ci

dev-api: ## run the api with reload on :8000
	cd $(API) && .venv/bin/alembic upgrade head && .venv/bin/uvicorn timesheets.main:app --reload

dev-web: ## run the vite dev server on :5173
	cd $(WEB) && npm run dev

test: test-api test-web ## run all tests

test-api: ## api tests (needs TEST_DATABASE_URL)
	cd $(API) && .venv/bin/pytest -q

test-web: ## web tests
	cd $(WEB) && npm test

lint: ## lint and check formatting
	cd $(API) && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd $(WEB) && npm run lint && npm run format:check && npm run typecheck

format: ## format api and web code
	cd $(API) && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
	cd $(WEB) && npm run format

up: ## start everything with docker compose
	docker compose up -d --build

down: ## stop docker compose
	docker compose down
