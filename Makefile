# huntRED® v2 - Makefile
# La Primera Plataforma de Nómina Conversacional del Mundo

.PHONY: help install install-dev test test-unit test-integration test-e2e lint format type-check security clean docker-build docker-up docker-down docs serve

# Default target
help: ## Show this help message
	@echo "huntRED® v2 - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test: ## Run all tests
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	pytest tests/e2e/ -v

test-watch: ## Run tests in watch mode
	pytest-watch tests/ --cov=src

# Code Quality
lint: ## Run linter (flake8)
	flake8 src/ tests/

format: ## Format code (black + isort)
	black src/ tests/
	isort src/ tests/

format-check: ## Check code formatting
	black --check src/ tests/
	isort --check-only src/ tests/

type-check: ## Run type checker (mypy)
	mypy src/

security: ## Run security checks (bandit)
	bandit -r src/

check: format-check lint type-check security ## Run all code quality checks

# Docker
docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in main container
	docker-compose exec app bash

# Database
db-migrate: ## Run database migrations
	alembic upgrade head

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(name)"

db-reset: ## Reset database (DANGER: removes all data)
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	alembic upgrade head

# Development
serve: ## Start development server
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start production server
	gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

celery-worker: ## Start Celery worker
	celery -A src.tasks.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	celery -A src.tasks.celery_app beat --loglevel=info

# Documentation
docs: ## Generate documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

# Utilities
clean: ## Clean cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/

requirements: ## Update requirements.txt from pyproject.toml
	pip-compile --upgrade

seed-db: ## Seed database with sample data
	python scripts/seed_database.py

setup-dev: install-dev db-migrate seed-db ## Complete development setup

# CI/CD
ci-test: ## Run tests for CI environment
	pytest tests/ --cov=src --cov-report=xml --cov-report=term

ci-lint: ## Run linting for CI environment
	flake8 src/ tests/ --output-file=flake8-report.txt

ci-security: ## Run security checks for CI environment
	bandit -r src/ -f json -o bandit-report.json

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add deployment commands here

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	# Add deployment commands here

# Monitoring
logs: ## View application logs
	tail -f logs/huntred.log

monitor: ## Open monitoring dashboard
	@echo "Opening Grafana dashboard..."
	open http://localhost:3001

# Data
backup-db: ## Backup database
	docker-compose exec db pg_dump -U huntred_user huntred_v2 > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database from backup (specify file with FILE=backup.sql)
	docker-compose exec -T db psql -U huntred_user huntred_v2 < $(FILE)

# Performance
benchmark: ## Run performance benchmarks
	python scripts/benchmark.py

profile: ## Profile application performance
	python scripts/profile_app.py

# Release
version-patch: ## Bump patch version
	bump2version patch

version-minor: ## Bump minor version
	bump2version minor

version-major: ## Bump major version
	bump2version major

release: ## Create release (specify version with VERSION=x.y.z)
	git tag -a v$(VERSION) -m "Release version $(VERSION)"
	git push origin v$(VERSION)

# Quick commands for daily development
dev: docker-up ## Start development environment
	@echo "🚀 huntRED® v2 development environment started!"
	@echo "📱 API: http://localhost:8000"
	@echo "📊 Docs: http://localhost:8000/docs"
	@echo "🔍 Grafana: http://localhost:3001"
	@echo "🐘 pgAdmin: http://localhost:5050"

stop: docker-down ## Stop development environment
	@echo "🛑 huntRED® v2 development environment stopped!"

status: ## Show status of all services
	docker-compose ps