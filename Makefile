.PHONY: help dev test lint format build clean docker-up docker-down

help:
	@echo "Career-OS Development Commands:"
	@echo "  make dev          Start backend and frontend development servers"
	@echo "  make test         Run all Python unit and integration tests"
	@echo "  make lint         Run ruff checks and mypy static type analysis"
	@echo "  make format       Format code using ruff"
	@echo "  make build        Build frontend production assets"
	@echo "  make docker-up    Start full stack with Docker Compose"
	@echo "  make docker-down  Stop Docker Compose services"
	@echo "  make clean        Remove cache and build artifacts"

dev:
	@echo "Starting Career-OS services..."
	@echo "Run 'uvicorn app.main:app --reload' in backend/ and 'npm run dev' in frontend/"

test:
	./.venv/bin/pytest backend

lint:
	./.venv/bin/ruff format --check backend
	./.venv/bin/ruff check backend
	./.venv/bin/mypy backend

format:
	./.venv/bin/ruff format backend
	./.venv/bin/ruff check --fix backend

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
