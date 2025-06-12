# hypexbt Monorepo Makefile

.PHONY: help install install-dev lint format type-check test build-api run-api stop-api clean-api test-api logs-api check-all

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
	@echo "Docker API:"
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

# API targets
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