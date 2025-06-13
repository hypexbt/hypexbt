# hypexbt Monorepo Makefile

.PHONY: help install install-dev lint format type-check test build-api run-api stop-api clean-api test-api logs-api check-all redis-start redis-stop redis-logs redis-cli redis-clean dev-full compose-backend compose-down compose-logs compose-redis-only

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install       - Install dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Format code with ruff"
	@echo "  type-check    - Run mypy type checker"
	@echo "  test          - Run tests"
	@echo "  check-all     - Run all checks (lint, format, type-check, test)"
	@echo ""
	@echo "Redis:"
	@echo "  redis-start   - Start Redis container"
	@echo "  redis-stop    - Stop Redis container"
	@echo "  redis-logs    - Show Redis logs"
	@echo "  redis-cli     - Connect to Redis CLI"
	@echo "  redis-clean   - Stop and remove Redis container"
	@echo ""
	@echo "Docker Compose:"
	@echo "  compose-backend - Start all backend services with docker-compose"
	@echo "  compose-down  - Stop all services with docker-compose"
	@echo "  compose-logs  - Show logs from all services"
	@echo "  compose-redis-only - Start only Redis with docker-compose"
	@echo ""
	@echo "Application:"
	@echo "  dev-full      - Start Redis + Application for development"
	@echo "  run-app       - Run the application (requires Redis)"
	@echo "  test-app      - Test all application endpoints"
	@echo ""
	@echo "Docker API (Legacy):"
	@echo "  build-api     - Build the API Docker image"
	@echo "  run-api       - Run the API container"
	@echo "  stop-api      - Stop and remove the API container"
	@echo "  clean-api     - Remove API container and image"
	@echo "  test-api      - Test the API endpoints"
	@echo "  logs-api      - Show logs from the API container"
	@echo "  dev-api       - Quick development workflow for API"

# Development targets
install:
	@echo "Installing dependencies..."
	uv sync

install-dev:
	@echo "Installing development dependencies..."
	uv sync --dev

lint:
	@echo "Running ruff linter..."
	uv run ruff check .

format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

type-check:
	@echo "Running mypy type checker..."
	uv run mypy . --config-file pyproject.toml

test:
	@echo "Running tests..."
	uv run pytest

check-all: lint type-check test
	@echo "All checks completed!"

# Redis targets
redis-start:
	@echo "Starting Redis container..."
	@if ! docker info >/dev/null 2>&1; then \
		echo "❌ Docker is not running. Please start Docker Desktop first."; \
		exit 1; \
	fi
	docker run -d --name hypexbt-redis -p 6379:6379 redis:7-alpine
	@echo "✅ Redis started on port 6379"
	@echo "Test with: make redis-cli"

redis-stop:
	@echo "Stopping Redis container..."
	-docker stop hypexbt-redis

redis-logs:
	@echo "Redis container logs:"
	docker logs hypexbt-redis

redis-cli:
	@echo "Connecting to Redis CLI (type 'exit' to quit):"
	docker exec -it hypexbt-redis redis-cli

redis-clean: redis-stop
	@echo "Removing Redis container..."
	-docker rm hypexbt-redis

# Docker Compose targets (alternative to individual containers)
compose-backend:
	@echo "Starting all services with docker-compose..."
	cd docker && docker compose up -d
	@echo "✅ Services started:"
	@echo "  Redis: localhost:6379"
	@echo "  App: localhost:8000"

compose-down:
	@echo "Stopping all services..."
	cd docker && docker compose down

compose-logs:
	@echo "Service logs:"
	cd docker && docker compose logs -f

compose-redis-only:
	@echo "Starting only Redis with docker-compose..."
	cd docker && docker compose up -d redis
	@echo "✅ Redis started on port 6379"

# Application targets
run-app:
	@echo "Starting hypexbt application..."
	@echo "Make sure Redis is running: make redis-start"
	uv run python -m src.main

dev-full: redis-clean redis-start
	@echo "Development environment ready!"
	@echo "Redis: http://localhost:6379"
	@echo ""
	@echo "To start the application:"
	@echo "  make run-app"
	@echo ""
	@echo "To test Redis:"
	@echo "  make redis-cli"

test-app:
	@echo "Testing application endpoints..."
	@echo "Root endpoint:"
	curl -s http://localhost:8000/ | python3 -m json.tool
	@echo -e "\nHealth endpoint:"
	curl -s http://localhost:8000/health | python3 -m json.tool
	@echo -e "\nStatus endpoint:"
	curl -s http://localhost:8000/api/status | python3 -m json.tool
	@echo -e "\nEcho endpoint:"
	curl -s http://localhost:8000/api/echo/hello-world | python3 -m json.tool
	@echo -e "\nTweet endpoint:"
	curl -s -X POST http://localhost:8000/api/tweet \
		-H "Content-Type: application/json" \
		-d '{"content": "Test tweet from Makefile!", "priority": 2}' | python3 -m json.tool

# Legacy API targets (keeping for compatibility)
build-api:
	@echo "Building API Docker image..."
	docker build -f docker/Dockerfile.api -t hypexbt-api .

run-api:
	@echo "Running API container..."
	docker run -d -p 8000:8000 --name hypexbt-api-container hypexbt-api

stop-api:
	@echo "Stopping API container..."
	-docker stop hypexbt-api-container
	-docker rm hypexbt-api-container

clean-api: stop-api
	@echo "Removing API image..."
	-docker rmi hypexbt-api

test-api:
	@echo "Testing API endpoints..."
	@echo "Root endpoint:"
	curl -s http://localhost:8000/ | python3 -m json.tool
	@echo -e "\nHealth endpoint:"
	curl -s http://localhost:8000/health | python3 -m json.tool
	@echo -e "\nEcho endpoint:"
	curl -s http://localhost:8000/api/echo/hello-world | python3 -m json.tool

logs-api:
	@echo "API container logs:"
	docker logs hypexbt-api-container

# Quick development workflow
dev-api: stop-api build-api run-api
	@echo "API development environment ready!"
	@echo "API running at http://localhost:8000" 