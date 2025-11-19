# Telegram Quiz NFT Platform - Makefile
# Quick commands for development using uv

.PHONY: help install install-dev test lint format type-check clean run-bot run-api docker-up docker-down migration

# Default target
help:
	@echo "🎯 Telegram Quiz NFT Platform - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install all dependencies (prod + dev)"
	@echo ""
	@echo "Development:"
	@echo "  make run-bot          Run Telegram bot"
	@echo "  make run-api          Run FastAPI server"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Format code with ruff & black"
	@echo "  make type-check       Run mypy type checker"
	@echo "  make check            Run all checks (lint + type-check + test)"
	@echo ""
	@echo "Database:"
	@echo "  make migration MSG='message'  Create new migration"
	@echo "  make migrate          Apply pending migrations"
	@echo "  make migrate-down     Rollback last migration"
	@echo "  make seed             Seed database with sample data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start PostgreSQL & Redis"
	@echo "  make docker-down      Stop all Docker services"
	@echo "  make docker-logs      Show Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove cache and build files"

# Installation
install:
	@echo "📦 Installing production dependencies with uv..."
	cd backend && uv pip install -e .

install-dev:
	@echo "📦 Installing all dependencies with uv..."
	cd backend && uv pip install -e ".[dev]"

# Running services
run-bot:
	@echo "🤖 Starting Telegram bot..."
	cd backend && uv run python -m app.bot.main

run-api:
	@echo "🚀 Starting FastAPI server..."
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	@echo "🧪 Running tests..."
	cd backend && uv run pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: backend/htmlcov/index.html"

# Code quality
lint:
	@echo "🔍 Running ruff linter..."
	cd backend && uv run ruff check .

format:
	@echo "✨ Formatting code..."
	cd backend && uv run ruff format .
	cd backend && uv run black .

type-check:
	@echo "📝 Running mypy type checker..."
	cd backend && uv run mypy app/

check: lint type-check test
	@echo "✅ All checks passed!"

# Database migrations
migration:
	@echo "📝 Creating new migration: $(MSG)"
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

migrate:
	@echo "⬆️  Applying migrations..."
	cd backend && uv run alembic upgrade head

migrate-down:
	@echo "⬇️  Rolling back last migration..."
	cd backend && uv run alembic downgrade -1

seed:
	@echo "🌱 Seeding database with sample data..."
	cd backend && uv run python -m app.db.seed

# Docker
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ PostgreSQL running on localhost:5432"
	@echo "✅ Redis running on localhost:6379"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "📋 Docker logs..."
	docker-compose logs -f

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✨ Cleanup complete!"
