# AI Agent Automation Hub - Makefile
# Provides common development and deployment tasks

.PHONY: help install install-dev test lint format clean build run-bot setup-db docker-build docker-up docker-down deploy-pi health-check

# Default target
help:
	@echo "AI Agent Automation Hub - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development:"
	@echo "  install        Install package in editable mode"
	@echo "  install-dev    Install package with development dependencies"
	@echo "  test          Run all tests"
	@echo "  lint          Run linting (flake8, mypy)"
	@echo "  format        Format code (black, isort)"
	@echo "  clean         Clean build artifacts and cache files"
	@echo ""
	@echo "Application:"
	@echo "  run-bot       Run the Discord bot"
	@echo "  setup-db      Initialize the database"
	@echo "  health-check  Check system health"
	@echo "  validate-deployment  Run comprehensive deployment validation"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start all services with Docker Compose"
	@echo "  docker-down   Stop all Docker services"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-pi     Deploy to Raspberry Pi 5 (requires SSH config)"
	@echo "  build         Build distribution packages"
	@echo ""

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev,all]

# Development targets
test:
	pytest tests/ -v --cov=. --cov-report=term-missing

test-fast:
	pytest tests/ -v -x --no-cov

lint:
	flake8 agents/ bot/ database/ scripts/ --max-line-length=88 --extend-ignore=E203,W503
	mypy agents/ bot/ database/ scripts/ --ignore-missing-imports

format:
	black agents/ bot/ database/ scripts/ examples/
	isort agents/ bot/ database/ scripts/ examples/

format-check:
	black --check agents/ bot/ database/ scripts/ examples/
	isort --check-only agents/ bot/ database/ scripts/ examples/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage .pytest_cache/ .mypy_cache/

# Application targets
run-bot:
	python -m bot.run_bot

run-bot-debug:
	python -m bot.run_bot --debug

setup-db:
	python scripts/init_database.py

health-check:
	python -m deploy.health_check

validate-deployment:
	python scripts/validate_deployment.py

validate-deployment-json:
	python scripts/validate_deployment.py --json

# Docker targets
docker-build:
	docker build -t ai-automation-hub .

docker-up:
	docker-compose up -d

docker-up-full:
	docker-compose --profile full up -d

docker-up-monitoring:
	docker-compose --profile monitoring up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Build and distribution
build: clean
	python -m build

build-wheel:
	python -m build --wheel

build-sdist:
	python -m build --sdist

# Development setup
dev-setup: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

# Deployment targets
deploy-pi:
	@echo "Deploying to Raspberry Pi..."
	@if [ -z "$(PI_HOST)" ]; then \
		echo "Error: PI_HOST not set. Usage: make deploy-pi PI_HOST=pi@192.168.1.100"; \
		exit 1; \
	fi
	rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' . $(PI_HOST):~/ai-automation-hub/
	ssh $(PI_HOST) "cd ~/ai-automation-hub && bash deploy/pi-setup.sh"

# Environment setup
env-create:
	@echo "Creating .env file from template..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi

# Database management
db-migrate:
	python database/migrations/init_schema.py

db-reset:
	@echo "⚠️  This will delete all data. Are you sure? [y/N]"
	@read confirm && [ "$$confirm" = "y" ] || exit 1
	python scripts/init_database.py --reset

# Monitoring and maintenance
monitor:
	python scripts/monitor_testing_agent.py

check-agents:
	python scripts/check_testing_agent.py

validate-discord:
	python scripts/validate_discord_implementation.py

validate-testing:
	python scripts/validate_testing_agent.py

# Security and compliance
security-scan:
	pip-audit
	bandit -r agents/ bot/ database/ scripts/

pre-commit-all:
	pre-commit run --all-files

# Documentation
docs-serve:
	@echo "Serving documentation on http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	python -m http.server 8000 --directory docs/

# Quick development workflow
dev: format lint test
	@echo "✅ Development checks passed!"

ci: format-check lint test
	@echo "✅ CI checks passed!"

# Release workflow
release-check: clean build
	twine check dist/*

# System requirements check
check-deps:
	@echo "Checking system dependencies..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
	@command -v pip >/dev/null 2>&1 || { echo "❌ pip is required but not installed."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "⚠️  Docker is not installed (optional for development)."; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "⚠️  Docker Compose is not installed (optional for development)."; }
	@echo "✅ System dependencies check complete!"

# Show project status
status:
	@echo "Project Status:"
	@echo "==============="
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Git status: $$(git status --porcelain 2>/dev/null | wc -l || echo '0') modified files"
	@echo "Docker status: $$(docker-compose ps --services --filter 'status=running' 2>/dev/null | wc -l || echo '0') running services"
	@echo ""
	@echo "Recent commits:"
	@git log --oneline -5 2>/dev/null || echo "No git history available"