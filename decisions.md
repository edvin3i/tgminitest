# Architectural Decision Records (ADR)

This document records all important architectural and technical decisions made during the development of the Telegram Quiz NFT Platform.

---

## ADR Format

Each decision follows this structure:
- **Status**: Proposed / Accepted / Deprecated / Superseded
- **Date**: When the decision was made
- **Context**: What prompted this decision
- **Decision**: What we decided to do
- **Consequences**: Positive and negative outcomes
- **Alternatives Considered**: What else we looked at

---

## ADR-001: Use Aiogram 3.x for Telegram Bot

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Architecture Team

### Context
We need a robust, modern framework for building the Telegram bot component. The bot needs to:
- Handle complex conversation flows (quiz sessions)
- Support inline keyboards and callbacks
- Manage user sessions
- Scale to thousands of concurrent users
- Integrate with async database operations

### Decision
Use **Aiogram 3.x** as the primary framework for the Telegram bot.

### Consequences

**Positive:**
- Modern async/await support (fully async)
- Excellent documentation and community
- Built-in FSM (Finite State Machine) for conversation flows
- Type hints and Pydantic integration
- Active development and maintenance
- Easy integration with FastAPI (both use async)

**Negative:**
- Breaking changes from Aiogram 2.x (migration path exists)
- Learning curve for team members new to the framework
- Some third-party libraries may not support v3 yet

### Alternatives Considered

1. **python-telegram-bot**
   - Rejected: Less modern async support
   - More verbose code for complex flows

2. **Telethon**
   - Rejected: More low-level, overkill for bot
   - Better suited for user accounts, not bots

3. **Custom implementation with `requests`**
   - Rejected: Reinventing the wheel
   - Too much boilerplate code

---

## ADR-002: Use FastAPI for Backend API

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Architecture Team

### Context
We need a separate API layer for:
- Admin panel (React frontend)
- Telegram WebApp integration
- Webhook handling (TON, payment callbacks)
- Future mobile app support
- Analytics and reporting

### Decision
Use **FastAPI** as the backend API framework, running separately from the Aiogram bot but sharing the same database and business logic.

### Consequences

**Positive:**
- Automatic API documentation (OpenAPI/Swagger)
- Excellent async support
- Type safety with Pydantic
- High performance (comparable to Node.js)
- Easy testing with TestClient
- Great integration with SQLAlchemy 2.0 async

**Negative:**
- Two separate processes to manage (bot + API)
- Slightly more complex deployment
- Need to share code between bot and API

### Alternatives Considered

1. **Django REST Framework**
   - Rejected: Heavier framework
   - Less suitable for async operations
   - Slower than FastAPI

2. **Flask**
   - Rejected: Older, less modern
   - Limited async support
   - Less type safety

3. **Combine everything in Aiogram**
   - Rejected: Aiogram not designed for REST API
   - Would create tight coupling
   - Harder to scale independently

### Implementation Notes
- Bot and API will be separate entry points
- Shared code in `app/services/`, `app/models/`
- Docker Compose will manage both services

---

## ADR-003: PostgreSQL as Primary Database

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Architecture Team

### Context
Need a robust database for storing:
- User profiles
- Quizzes, questions, answers
- Quiz results and scores
- NFT transaction records
- Complex relationships between entities

### Decision
Use **PostgreSQL 17** as the primary database with **SQLAlchemy 2.0** async ORM.

### Consequences

**Positive:**
- ACID compliance for critical data (NFT transactions)
- Excellent JSON support (JSONB) for flexible schemas
- Strong community and ecosystem
- Great performance with proper indexing
- Advanced features (full-text search, materialized views)
- Excellent async support via asyncpg

**Negative:**
- More complex setup than SQLite
- Requires separate service (Docker container)
- Need to manage backups

### Alternatives Considered

1. **MongoDB**
   - Rejected: Eventual consistency issues
   - Less suitable for transactional data
   - Relationships harder to manage

2. **SQLite**
   - Rejected: Not production-ready for concurrent access
   - Limited for scaling

3. **MySQL**
   - Rejected: Less advanced JSON support
   - PostgreSQL generally preferred in Python ecosystem

---

## ADR-004: Redis for Session State and Caching

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Architecture Team

### Context
Need fast, temporary storage for:
- Active quiz sessions (current question, answers so far)
- User authentication sessions
- API response caching
- Rate limiting counters

### Decision
Use **Redis 8** for all session state and caching needs.

### Consequences

**Positive:**
- Extremely fast (in-memory)
- Built-in TTL (time-to-live) for automatic cleanup
- Support for complex data structures (hashes, sets, sorted sets)
- Great for rate limiting
- Pub/sub for real-time features (future)

**Negative:**
- Additional service to manage
- Data is not persisted by default
- Memory constraints (need monitoring)

### Alternatives Considered

1. **In-memory Python dictionaries**
   - Rejected: Lost on restart
   - Can't share between bot and API processes

2. **PostgreSQL for sessions**
   - Rejected: Too slow for high-frequency operations
   - Would create unnecessary database load

3. **Memcached**
   - Rejected: Less feature-rich than Redis
   - Redis better suited for our use cases

---

## ADR-005: Pytoniq for TON Blockchain Integration

**Status**: Proposed
**Date**: 2025-11-18
**Decider**: Blockchain Team

### Context
Need to interact with TON blockchain for:
- Minting NFTs
- Verifying payments
- Reading NFT data
- Managing wallets

### Decision
Use **pytoniq** library for TON blockchain interactions initially, with option to evaluate **tonapi** or **toncenter** if needed.

### Consequences

**Positive:**
- Pure Python library
- Direct blockchain interaction
- Good documentation
- Active maintenance

**Negative:**
- Less mature than some alternatives
- May need to switch if limitations found
- Learning curve for TON-specific concepts

### Alternatives Considered

1. **tonapi**
   - Alternative: API-based approach
   - Pros: Simpler, less code
   - Cons: Dependency on third-party service

2. **toncenter**
   - Alternative: Official TON HTTP API
   - Pros: Official support
   - Cons: Less Pythonic

3. **ton-kotlin SDK via bridge**
   - Rejected: Too complex
   - Language interop overhead

### Notes
- Decision may be revisited in Phase 3 during TON integration
- Will evaluate based on:
  - Ease of NFT minting
  - Transaction reliability
  - Documentation quality
  - Community support

---

## ADR-006: React + TypeScript for Frontend

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Frontend Team

### Context
Need a modern web interface for:
- Admin panel (quiz management)
- User WebApp (Telegram mini-app)
- Responsive design
- Real-time updates

### Decision
Use **React 18+ with TypeScript** and **Vite** as the build tool.

### Consequences

**Positive:**
- Type safety with TypeScript
- Large ecosystem of libraries
- Great developer experience
- Fast build times with Vite
- Easy Telegram WebApp SDK integration
- Server-side rendering possible (if needed)

**Negative:**
- Build step required
- Bundle size considerations
- TypeScript learning curve for some

### Alternatives Considered

1. **Vue.js**
   - Pros: Simpler learning curve
   - Cons: Smaller ecosystem, less demand

2. **Svelte**
   - Pros: Smaller bundle size
   - Cons: Smaller community, fewer libraries

3. **Plain HTML/JS**
   - Rejected: Too limited for complex UI
   - No type safety

4. **Next.js**
   - Considered: Overkill for this project
   - May revisit if SSR needed

---

## ADR-007: Monorepo vs Multi-Repo Structure

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: DevOps Team

### Context
Need to decide on repository structure for:
- Backend (Python)
- Frontend (React)
- Documentation
- Infrastructure (Docker configs)

### Decision
Use a **monorepo** structure with all components in a single repository.

### Consequences

**Positive:**
- Easier to maintain version consistency
- Atomic commits across frontend/backend
- Simpler CI/CD setup
- Better documentation co-location
- Easier for new developers

**Negative:**
- Single CI/CD pipeline for different languages
- Larger repository size
- Potential for accidental cross-concerns

### Structure
```
telegram-quiz-nft/
├── backend/          # Python FastAPI + Aiogram
├── frontend/         # React TypeScript
├── docs/             # Documentation
├── docker-compose.yml
└── .github/workflows/  # CI/CD
```

### Alternatives Considered

1. **Multi-repo (separate repos)**
   - Rejected: More complex to coordinate
   - Harder to maintain consistency
   - More overhead for small team

2. **Backend and Frontend in same folder**
   - Rejected: Harder to isolate builds
   - Messy file structure

---

## ADR-008: Docker Compose for Development

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: DevOps Team

### Context
Need consistent development environment across team members with:
- PostgreSQL
- Redis
- Backend services
- Frontend (optional in dev)

### Decision
Use **Docker Compose** for local development environment.

### Consequences

**Positive:**
- Consistent environment across team
- Easy onboarding for new developers
- Isolated services
- Simple commands (`docker-compose up`)
- Production-like environment locally

**Negative:**
- Requires Docker knowledge
- Initial setup time
- Resource usage on developer machines
- Slightly slower than native development

### docker-compose.yml Structure
```yaml
services:
  postgres:
    image: postgres:16
  redis:
    image: redis:7-alpine
  backend:
    build: ./backend
  bot:
    build: ./backend
    command: python -m app.bot
  frontend:
    build: ./frontend
```

### Alternatives Considered

1. **Local installation (Postgres, Redis locally)**
   - Rejected: Inconsistent across environments
   - Hard to version

2. **Kubernetes (K8s) for dev**
   - Rejected: Overkill for local development
   - Too complex

3. **Vagrant**
   - Rejected: Heavier than Docker
   - Less modern

---

## ADR-009: Pydantic for Data Validation

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Backend Team

### Context
Need robust data validation for:
- API request/response schemas
- Configuration management
- Database model validation
- Telegram webhook data

### Decision
Use **Pydantic V2** for all data validation and serialization.

### Consequences

**Positive:**
- Type-safe validation
- Automatic OpenAPI schema generation
- Excellent error messages
- Performance improvements in V2
- Great integration with FastAPI
- Supports both validation and serialization

**Negative:**
- Learning curve for advanced features
- Migration from V1 to V2 if needed

### Usage Areas
1. FastAPI request/response models
2. Settings/configuration (`pydantic-settings`)
3. Business logic DTOs (Data Transfer Objects)

### Alternatives Considered

1. **Marshmallow**
   - Rejected: More verbose
   - Less modern than Pydantic

2. **Dataclasses + manual validation**
   - Rejected: Too much boilerplate
   - No automatic validation

3. **JSON Schema**
   - Rejected: Less Pythonic
   - Harder to maintain

---

## ADR-010: Alembic for Database Migrations

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Backend Team

### Context
Need version control for database schema with:
- Automatic migration generation
- Rollback capability
- Team collaboration on schema changes

### Decision
Use **Alembic** for database migrations with async support.

### Consequences

**Positive:**
- Auto-generate migrations from SQLAlchemy models
- Version control for schema
- Easy rollback
- Team-friendly (migrations in git)
- Supports async operations

**Negative:**
- Needs careful review of auto-generated migrations
- Conflicts possible when multiple devs create migrations
- Additional step in development workflow

### Workflow
```bash
# Create migration
alembic revision --autogenerate -m "Add NFT table"

# Review generated SQL
# Edit if needed

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Alternatives Considered

1. **Raw SQL scripts**
   - Rejected: Manual work
   - No auto-generation

2. **Django migrations**
   - Rejected: Requires Django

3. **SQLAlchemy-migrate**
   - Rejected: Deprecated in favor of Alembic

---

## ADR-011: Structured Logging with Loguru

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Backend Team

### Context
Need comprehensive logging for:
- Debugging issues
- Monitoring application health
- Audit trails (NFT minting)
- Error tracking

### Decision
Use **Loguru** for all application logging with structured output.

### Consequences

**Positive:**
- Simple, intuitive API
- Automatic serialization of objects
- Colored output for development
- JSON formatting for production
- Async support
- Exception capturing

**Negative:**
- Another dependency
- Different from standard library logging

### Configuration
```python
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="500 MB",
    level="INFO",
    format="{time} {level} {message}",
    serialize=True  # JSON format
)

logger.info("User took quiz", user_id=123, quiz_id=45, score=85)
```

### Alternatives Considered

1. **Python `logging` module**
   - Pros: Standard library
   - Cons: More boilerplate, less intuitive

2. **structlog**
   - Pros: Powerful structured logging
   - Cons: More complex configuration

3. **Print statements**
   - Rejected: Not production-ready

---

## ADR-012: Pytest for Testing Framework

**Status**: Accepted
**Date**: 2025-11-18
**Decider**: Backend Team

### Context
Need comprehensive testing framework for:
- Unit tests
- Integration tests
- Async test support
- Fixtures and mocking

### Decision
Use **pytest** with **pytest-asyncio** for all backend testing.

### Consequences

**Positive:**
- Simple, intuitive syntax
- Excellent async support
- Rich ecosystem of plugins
- Fixtures for code reuse
- Parametrized tests
- Great error messages

**Negative:**
- Different from unittest (stdlib)
- Learning curve for fixtures

### Key Plugins
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities

### Alternatives Considered

1. **unittest**
   - Rejected: More verbose
   - Less modern

2. **nose2**
   - Rejected: Less active development

---

## 📝 Decision Template

Use this template for future ADRs:

```markdown
## ADR-XXX: [Title]

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Decider**: [Team/Person]

### Context
[What prompted this decision? What problem are we solving?]

### Decision
[What did we decide to do?]

### Consequences

**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative:**
- [Trade-off 1]
- [Trade-off 2]

### Alternatives Considered

1. **[Alternative 1]**
   - [Why rejected]

2. **[Alternative 2]**
   - [Why rejected]

### Notes
[Any additional context or future considerations]
```

---

## 🔄 Review Process

**Who can create ADRs**: Any team member
**Review required**: Yes, at least one other developer
**When to create**:
- Major technology choice
- Architecture pattern decision
- Infrastructure changes
- Breaking changes to APIs

**When NOT to create**:
- Minor refactoring
- Bug fixes
- Small feature additions
- Code style preferences

---

## 📚 References

- [Architectural Decision Records](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
