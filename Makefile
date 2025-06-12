# hypexbt Monorepo Makefile

.PHONY: help build-api run-api stop-api clean-api test-api logs-api

# Default target
help:
	@echo "Available commands:"
	@echo "  build-api     - Build the API Docker image"
	@echo "  run-api       - Run the API container"
	@echo "  stop-api      - Stop and remove the API container"
	@echo "  clean-api     - Remove API container and image"
	@echo "  test-api      - Test the API endpoints"
	@echo "  logs-api      - Show logs from the API container"

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