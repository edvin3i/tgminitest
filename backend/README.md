# Telegram Quiz NFT Platform - Backend

Backend services for the Telegram Quiz NFT Platform, including:

- **FastAPI REST API** - Quiz management, user profiles, and NFT operations
- **Telegram Bot** - Interactive quiz experience via Aiogram 3
- **Database** - PostgreSQL with SQLAlchemy 2.0 async ORM
- **State Management** - Redis for quiz session state

## Quick Start

See the main [README.md](../README.md) and [QUICKSTART.md](../QUICKSTART.md) for setup instructions.

## Development

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run API server
uv run uvicorn app.main:app --reload

# Run bot
uv run python -m app.bot.main
```

## Project Structure

- `app/` - Application code
  - `api/` - FastAPI REST API
  - `bot/` - Telegram bot handlers
  - `models/` - SQLAlchemy models
  - `schemas/` - Pydantic schemas
  - `services/` - Business logic
  - `db/` - Database configuration and migrations
- `tests/` - Test suite
- `alembic/` - Database migrations

## Documentation

- [API Documentation](../API.md)
- [Architecture](../architecture.md)
- [Development Guidelines](../CLAUDE.md)
