.PHONY: help dev test lint format build clean docker-up docker-down run-backend run-frontend run-worker

# Include .env if present and export variables to child processes
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

help:
	@echo "Career-OS Development Commands:"
	@echo "  make dev           Verify environment (.env) and display start commands"
	@echo "  make run-backend   Start FastAPI backend development server"
	@echo "  make run-worker    Start background ingestion worker daemon"
	@echo "  make run-frontend  Start Vite React frontend development server"
	@echo "  make test          Run all Python unit and integration tests"
	@echo "  make lint          Run ruff checks and mypy static type analysis"
	@echo "  make format        Format code using ruff"
	@echo "  make build         Build frontend production assets"
	@echo "  make docker-up     Start full stack with Docker Compose using .env"
	@echo "  make docker-down   Stop Docker Compose services"
	@echo "  make clean         Remove cache and build artifacts"

VENV ?= $(shell test -d backend/.venv && echo backend/.venv || echo .venv)

.env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Initialized .env from .env.example"; fi

dev: .env
	@echo "Career-OS environment verified (.env active)."
	@echo "Run 'make run-backend', 'make run-worker', and 'make run-frontend' to start development services."

run-backend: .env
	cd backend && ../$(VENV)/bin/uvicorn app.main:app --reload --host $(or $(HOST),0.0.0.0) --port $(or $(PORT),8000)

run-worker: .env
	cd backend && ../$(VENV)/bin/python -m app.ingestion.worker

run-frontend:
	cd frontend && npm run dev

test:
	./$(VENV)/bin/pytest backend

lint:
	./$(VENV)/bin/ruff format --check backend
	./$(VENV)/bin/ruff check backend
	./$(VENV)/bin/mypy backend

format:
	./$(VENV)/bin/ruff format backend
	./$(VENV)/bin/ruff check --fix backend

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf frontend/dist
