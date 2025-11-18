# Current Working Checklist

**Last Updated:** 2025-11-18
**Current Phase:** Phase 1 - Foundation & MVP Bot
**Sprint Goal:** Complete project setup and basic infrastructure

---

## 🎯 Today's Priorities

### High Priority (Do First)
- [ ] Create project directory structure
- [ ] Set up Python environment with dependencies
- [ ] Initialize Git repository and first commit
- [ ] Create `.env.example` with all required variables
- [ ] Set up Docker Compose for PostgreSQL

### Medium Priority (Do Today)
- [ ] Design database schema (ERD)
- [ ] Create SQLAlchemy models
- [ ] Set up Alembic migrations
- [ ] Write initial migration
- [ ] Basic Aiogram bot skeleton

### Low Priority (Nice to Have)
- [ ] Set up pre-commit hooks
- [ ] Add README.md with setup instructions
- [ ] Configure linting (ruff)

---

## 📋 Week 1: Foundation Setup

### Day 1-2: Project Infrastructure ⏳
- [ ] **Project Structure**
  - [ ] Create `backend/` directory
  - [ ] Create `backend/app/` with `__init__.py`
  - [ ] Create `backend/tests/` directory
  - [ ] Create `frontend/` directory (placeholder)
  - [ ] Create `docs/` directory
  - [ ] Add `.gitignore` (Python, Node, .env, etc.)

- [ ] **Python Environment**
  - [ ] Create `requirements.txt` with:
    - [ ] aiogram==3.x
    - [ ] fastapi==0.104+
    - [ ] uvicorn[standard]
    - [ ] sqlalchemy==2.x
    - [ ] alembic
    - [ ] asyncpg
    - [ ] pydantic==2.x
    - [ ] pydantic-settings
    - [ ] python-dotenv
    - [ ] loguru
    - [ ] pytest
    - [ ] pytest-asyncio
    - [ ] httpx
  - [ ] Create `pyproject.toml` for project metadata
  - [ ] Set up virtual environment
  - [ ] Install dependencies

- [ ] **Docker Setup**
  - [ ] Create `docker-compose.yml`
  - [ ] Add PostgreSQL service
  - [ ] Add Redis service
  - [ ] Add pgAdmin (optional, for dev)
  - [ ] Test `docker-compose up -d`

- [ ] **Environment Configuration**
  - [ ] Create `.env.example` with:
    ```
    # Bot
    BOT_TOKEN=your_bot_token_here

    # Database
    POSTGRES_USER=quizbot
    POSTGRES_PASSWORD=changeme
    POSTGRES_DB=telegram_quiz
    DATABASE_URL=postgresql+asyncpg://quizbot:changeme@localhost:5432/telegram_quiz

    # Redis
    REDIS_URL=redis://localhost:6379/0

    # TON (for later)
    TON_API_KEY=
    TON_NETWORK=testnet
    NFT_COLLECTION_ADDRESS=

    # App
    DEBUG=True
    LOG_LEVEL=INFO
    ```
  - [ ] Add `.env` to `.gitignore`
  - [ ] Document environment variables

### Day 3-4: Database Schema & Models ⏳
- [ ] **Schema Design**
  - [ ] Draw ERD (Entity Relationship Diagram)
  - [ ] Define tables:
    - [ ] `users` table structure
    - [ ] `quizzes` table structure
    - [ ] `questions` table structure
    - [ ] `answers` table structure
    - [ ] `result_types` table structure
    - [ ] `quiz_results` table structure
    - [ ] `mint_transactions` table structure (for later)
    - [ ] `nft_metadata` table structure (for later)
  - [ ] Define indexes and foreign keys
  - [ ] Add to `architecture.md`

- [ ] **SQLAlchemy Models**
  - [ ] Create `backend/app/models/__init__.py`
  - [ ] Create `backend/app/models/base.py` (Base class)
  - [ ] Create `backend/app/models/user.py`
    ```python
    class User(Base):
        id: Mapped[int] = mapped_column(primary_key=True)
        telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
        username: Mapped[str | None]
        first_name: Mapped[str]
        last_name: Mapped[str | None]
        is_admin: Mapped[bool] = mapped_column(default=False)
        created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ```
  - [ ] Create `backend/app/models/quiz.py`
  - [ ] Create `backend/app/models/question.py`
  - [ ] Create `backend/app/models/answer.py`
  - [ ] Create `backend/app/models/result.py`
  - [ ] Add relationships between models

- [ ] **Database Connection**
  - [ ] Create `backend/app/db/database.py`
  - [ ] Implement async engine setup
  - [ ] Create session maker
  - [ ] Add connection health check
  - [ ] Add dependency injection for sessions

- [ ] **Alembic Setup**
  - [ ] Run `alembic init alembic`
  - [ ] Configure `alembic.ini`
  - [ ] Update `env.py` for async support
  - [ ] Create initial migration: `alembic revision --autogenerate -m "Initial schema"`
  - [ ] Test migration: `alembic upgrade head`
  - [ ] Test rollback: `alembic downgrade -1`

### Day 5-7: Basic Bot Implementation ⏳
- [ ] **Bot Structure**
  - [ ] Create `backend/app/bot/__init__.py`
  - [ ] Create `backend/app/bot/main.py` (bot entry point)
  - [ ] Create `backend/app/bot/handlers/__init__.py`
  - [ ] Create `backend/app/bot/keyboards/__init__.py`
  - [ ] Set up bot instance and dispatcher

- [ ] **Configuration**
  - [ ] Create `backend/app/config.py`
    ```python
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        BOT_TOKEN: str
        DATABASE_URL: str
        REDIS_URL: str
        DEBUG: bool = False

        class Config:
            env_file = ".env"
    ```
  - [ ] Test config loading

- [ ] **Basic Handlers**
  - [ ] Create `backend/app/bot/handlers/start.py`
    - [ ] `/start` command handler
    - [ ] Create/update user in database
    - [ ] Show welcome message
  - [ ] Create `backend/app/bot/handlers/help.py`
    - [ ] `/help` command handler
  - [ ] Create `backend/app/bot/handlers/quiz.py` (skeleton)
    - [ ] `/quiz` command handler
    - [ ] Show "Coming soon" message for now

- [ ] **Keyboards**
  - [ ] Create `backend/app/bot/keyboards/inline.py`
    - [ ] Main menu keyboard
    - [ ] Quiz selection keyboard (placeholder)

- [ ] **Bot Runner**
  - [ ] Create `backend/app/bot/main.py`
  - [ ] Set up logging with loguru
  - [ ] Start polling
  - [ ] Graceful shutdown handling
  - [ ] Test bot locally

- [ ] **User Service**
  - [ ] Create `backend/app/services/__init__.py`
  - [ ] Create `backend/app/services/user_service.py`
    ```python
    async def get_or_create_user(telegram_id: int, ...) -> User:
        # Check if exists, create if not
        pass
    ```
  - [ ] Add unit tests

---

## 📋 Week 2: Quiz Logic & Testing

### Day 8-10: Quiz System ⏳
- [ ] **Quiz Data Structure**
  - [ ] Create sample quiz JSON
  - [ ] Create seed script to populate DB
  - [ ] Add "Hogwarts House" quiz example

- [ ] **Quiz Service**
  - [ ] Create `backend/app/services/quiz_service.py`
  - [ ] `get_active_quizzes()` method
  - [ ] `get_quiz_by_id(quiz_id)` method
  - [ ] `calculate_result(quiz_id, answers)` method
  - [ ] `save_result(user_id, quiz_id, result)` method

- [ ] **Quiz State Management**
  - [ ] Implement Redis-based state storage
  - [ ] Store current question index
  - [ ] Store user answers
  - [ ] Add timeout handling (30 min TTL)

- [ ] **Quiz Handlers**
  - [ ] Update `backend/app/bot/handlers/quiz.py`
  - [ ] Show quiz list
  - [ ] Start quiz flow
  - [ ] Display questions one by one
  - [ ] Collect answers
  - [ ] Calculate and display result

- [ ] **Quiz Keyboards**
  - [ ] Update `backend/app/bot/keyboards/inline.py`
  - [ ] Quiz selection buttons
  - [ ] Answer option buttons
  - [ ] Navigation buttons (Next, Back)

### Day 11-12: Testing ⏳
- [ ] **Test Infrastructure**
  - [ ] Create `backend/tests/conftest.py`
  - [ ] Add database fixtures
  - [ ] Add async test client fixture
  - [ ] Add sample data fixtures

- [ ] **Unit Tests**
  - [ ] Test user service
    - [ ] Test user creation
    - [ ] Test user retrieval
  - [ ] Test quiz service
    - [ ] Test quiz retrieval
    - [ ] Test result calculation
    - [ ] Test different answer combinations

- [ ] **Integration Tests**
  - [ ] Test database operations
  - [ ] Test quiz flow end-to-end
  - [ ] Test state persistence

- [ ] **Coverage**
  - [ ] Set up pytest-cov
  - [ ] Aim for >80% coverage
  - [ ] Generate coverage report

### Day 13-14: Documentation & Refinement ⏳
- [ ] **Documentation**
  - [ ] Update README.md
    - [ ] Project description
    - [ ] Setup instructions
    - [ ] Running locally
    - [ ] Environment variables
  - [ ] Add inline code comments
  - [ ] Document quiz data format
  - [ ] Add API documentation (Swagger)

- [ ] **Code Quality**
  - [ ] Set up ruff for linting
  - [ ] Set up black for formatting
  - [ ] Set up mypy for type checking
  - [ ] Fix all linting errors
  - [ ] Add pre-commit hooks

- [ ] **Error Handling**
  - [ ] Add try-catch blocks
  - [ ] Add user-friendly error messages
  - [ ] Log errors properly
  - [ ] Handle database connection errors
  - [ ] Handle Telegram API errors

- [ ] **Testing & Demo**
  - [ ] Manual testing of all flows
  - [ ] Fix any bugs found
  - [ ] Prepare demo quiz
  - [ ] Test with real Telegram bot

---

## 🎯 Phase 1 Completion Checklist

Before moving to Phase 2, ensure:
- [ ] All tests passing (>80% coverage)
- [ ] Bot running without errors
- [ ] Users can start bot and register
- [ ] Users can browse and take quizzes
- [ ] Results are calculated correctly
- [ ] Results are saved to database
- [ ] Code is linted and formatted
- [ ] Documentation is complete
- [ ] Git history is clean with meaningful commits

---

## 🐛 Known Issues / Blockers

_None yet - will update as issues arise_

---

## 💡 Ideas / Future Enhancements

- [ ] Add quiz categories
- [ ] Add quiz difficulty levels
- [ ] Add quiz time limits
- [ ] Add leaderboard
- [ ] Add quiz search functionality

---

## 📝 Notes

- Remember to commit frequently with meaningful messages
- Run tests before each commit
- Update this file daily with progress
- Mark items with dates when completed
- Add notes for any deviations from plan

---

## ✅ Recently Completed

_Nothing yet - just getting started!_

---

**Next Review:** End of Week 1
**Blockers:** None
**Help Needed:** None
