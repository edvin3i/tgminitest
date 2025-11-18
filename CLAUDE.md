# CLAUDE.md - AI Assistant Coding & Testing Standards

## 🎯 Core Principles

This document defines **strict rules, standards, and behavior expectations** for the AI assistant working on the Telegram Quiz NFT Platform project.

---

## 📦 Package Management with uv

This project uses **[uv](https://docs.astral.sh/uv/)** - an extremely fast Python package installer and resolver written in Rust by Astral (the team behind Ruff).

### Why uv?
- ⚡ **10-100x faster** than pip
- 🔒 **Better dependency resolution** with proper lock files
- 🎯 **Modern Python tooling** from the Ruff creators
- 🚀 **Production-ready** and actively maintained

### Usage
```bash
# Install dependencies
uv pip install -e ".[dev]"

# Add a new package
uv pip install <package-name>

# Run commands without activating venv
uv run pytest
uv run python -m app.bot.main

# Update dependencies
uv pip install --upgrade -e ".[dev]"
```

### Important Notes
- ✅ **DO** use `uv` for all package installations
- ✅ **DO** update `pyproject.toml` when adding dependencies
- ✅ **DO** use `uv run` for running commands in CI/CD
- ❌ **DON'T** use `pip` unless absolutely necessary
- ❌ **DON'T** commit `requirements.txt` changes (use `pyproject.toml`)

---

## 🔒 Code Quality Standards

### ✅ DO

#### 1. **Type Safety**
```python
# ✅ GOOD: Proper type hints
from typing import Optional, List
from pydantic import BaseModel

class QuizResult(BaseModel):
    user_id: int
    quiz_id: int
    score: int
    result_type: str
    nft_minted: bool = False

async def get_user_results(user_id: int) -> List[QuizResult]:
    """Retrieve all quiz results for a user."""
    return await db.query(QuizResult).filter_by(user_id=user_id).all()
```

```python
# ❌ BAD: No type hints
def get_user_results(user_id):
    return db.query(QuizResult).filter_by(user_id=user_id).all()
```

#### 2. **Error Handling**
```python
# ✅ GOOD: Comprehensive error handling
from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    try:
        user_id = message.from_user.id
        user = await get_or_create_user(user_id)
        await message.answer(f"Welcome, {user.first_name}!")
    except DatabaseError as e:
        logger.error(f"Database error for user {message.from_user.id}: {e}")
        await message.answer("Sorry, something went wrong. Please try again.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await message.answer("An unexpected error occurred.")
```

```python
# ❌ BAD: No error handling
@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id)
    await message.answer(f"Welcome, {user.first_name}!")
```

#### 3. **Security - Telegram Data Validation**
```python
# ✅ GOOD: Validate Telegram WebApp data
import hmac
import hashlib
from fastapi import HTTPException

def validate_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData signature."""
    try:
        params = dict(item.split("=") for item in init_data.split("&"))
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items()) if k != "hash"
        )

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_hash != params.get("hash"):
            raise HTTPException(status_code=403, detail="Invalid signature")

        return params
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e}")
```

```python
# ❌ BAD: Trusting client data without validation
def get_user_from_webapp(init_data: str) -> dict:
    params = dict(item.split("=") for item in init_data.split("&"))
    return params  # No validation!
```

#### 4. **Database Operations - Use Transactions**
```python
# ✅ GOOD: Atomic operations with transactions
from sqlalchemy.ext.asyncio import AsyncSession

async def mint_nft_for_result(
    session: AsyncSession,
    user_id: int,
    result_id: int,
    nft_address: str
) -> bool:
    """Mint NFT and update database atomically."""
    async with session.begin():
        result = await session.get(QuizResult, result_id)
        if not result or result.nft_minted:
            raise ValueError("Invalid result or NFT already minted")

        # Create mint transaction record
        mint_tx = MintTransaction(
            user_id=user_id,
            result_id=result_id,
            nft_address=nft_address,
            status="completed"
        )
        session.add(mint_tx)

        # Update result
        result.nft_minted = True
        result.nft_address = nft_address

        await session.commit()

    return True
```

```python
# ❌ BAD: No transaction, inconsistent state possible
async def mint_nft_for_result(user_id: int, result_id: int, nft_address: str):
    result = await db.get(QuizResult, result_id)
    result.nft_minted = True
    await db.save(result)

    # If this fails, database is inconsistent!
    mint_tx = MintTransaction(...)
    await db.save(mint_tx)
```

#### 5. **Environment Configuration**
```python
# ✅ GOOD: Use Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # TON
    TON_API_KEY: str
    TON_NETWORK: str = "testnet"
    NFT_COLLECTION_ADDRESS: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

```python
# ❌ BAD: Hardcoded values or unsafe imports
import os

BOT_TOKEN = "123456:ABCDEF"  # Hardcoded!
DATABASE_URL = os.getenv("DATABASE_URL")  # No validation!
```

---

## 🧪 Testing Standards

### ✅ DO

#### 1. **Write Tests for All Critical Paths**
```python
# ✅ GOOD: Comprehensive test coverage
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_quiz_success(client: AsyncClient, admin_token: str):
    """Test successful quiz creation by admin."""
    response = await client.post(
        "/api/v1/quizzes",
        json={
            "title": "Hogwarts House Quiz",
            "description": "Find your house!",
            "questions": [
                {
                    "text": "What's your favorite color?",
                    "answers": [
                        {"text": "Red", "result_type": "gryffindor"},
                        {"text": "Green", "result_type": "slytherin"}
                    ]
                }
            ]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Hogwarts House Quiz"
    assert len(data["questions"]) == 1

@pytest.mark.asyncio
async def test_create_quiz_unauthorized(client: AsyncClient):
    """Test quiz creation fails without auth."""
    response = await client.post("/api/v1/quizzes", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_quiz_invalid_data(client: AsyncClient, admin_token: str):
    """Test quiz creation fails with invalid data."""
    response = await client.post(
        "/api/v1/quizzes",
        json={"title": ""},  # Empty title
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
```

#### 2. **Mock External Services**
```python
# ✅ GOOD: Mock TON blockchain interactions
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_mint_nft_success(mock_ton_client):
    """Test NFT minting with mocked TON client."""
    with patch('services.ton.mint_nft') as mock_mint:
        mock_mint.return_value = "EQD...ABC123"  # Mock NFT address

        result = await mint_nft_for_user(
            user_id=12345,
            result_id=1,
            metadata_uri="ipfs://..."
        )

        assert result.nft_address == "EQD...ABC123"
        mock_mint.assert_called_once()
```

```python
# ❌ BAD: Real blockchain calls in tests
async def test_mint_nft():
    # This will actually call TON blockchain!
    result = await mint_nft_for_user(user_id=12345, result_id=1)
    assert result.nft_address is not None  # Slow, unreliable, costly
```

#### 3. **Test Database Isolation**
```python
# ✅ GOOD: Use fixtures for clean database state
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Provide a clean database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_user_creation(db_session):
    """Test user creation in isolated database."""
    user = User(telegram_id=12345, username="testuser")
    db_session.add(user)
    await db_session.commit()

    result = await db_session.get(User, user.id)
    assert result.telegram_id == 12345
```

---

## 📁 Project Structure Standards

### ✅ DO

```
telegram-quiz-nft/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── quizzes.py
│   │   │   │   │   ├── users.py
│   │   │   │   │   ├── nft.py
│   │   │   │   └── router.py
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── quiz.py
│   │   │   ├── result.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── quiz.py
│   │   │   ├── user.py
│   │   ├── services/            # Business logic
│   │   │   ├── quiz_service.py
│   │   │   ├── ton_service.py
│   │   │   ├── nft_service.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── migrations/
│   │   └── bot/
│   │       ├── __init__.py
│   │       ├── main.py          # Aiogram bot
│   │       ├── handlers/
│   │       │   ├── start.py
│   │       │   ├── quiz.py
│   │       │   ├── nft.py
│   │       ├── keyboards/
│   │       │   ├── inline.py
│   │       └── middlewares/
│   ├── tests/
│   │   ├── api/
│   │   ├── bot/
│   │   ├── services/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
├── plan.md
├── architecture.md
├── todo.md
└── decisions.md
```

---

## 🚫 DON'T

### ❌ Anti-Patterns

1. **Don't mix business logic in handlers**
```python
# ❌ BAD
@router.message(F.text == "/quiz")
async def start_quiz(message: Message):
    # Too much logic in handler!
    quiz = await db.query(Quiz).filter_by(active=True).first()
    user = await db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        await db.add(user)
    # ... 50 more lines
```

```python
# ✅ GOOD
@router.message(F.text == "/quiz")
async def start_quiz(message: Message, quiz_service: QuizService):
    await quiz_service.start_quiz_for_user(message.from_user.id)
```

2. **Don't use `SELECT *`**
```python
# ❌ BAD
results = await db.execute("SELECT * FROM quiz_results")

# ✅ GOOD
results = await db.execute(
    select(QuizResult.id, QuizResult.score, QuizResult.result_type)
    .where(QuizResult.user_id == user_id)
)
```

3. **Don't ignore async/await**
```python
# ❌ BAD
def get_user(user_id: int):
    return db.query(User).get(user_id)  # Blocking!

# ✅ GOOD
async def get_user(user_id: int) -> User:
    async with AsyncSession() as session:
        return await session.get(User, user_id)
```

4. **Don't commit secrets**
```python
# ❌ BAD - in code
BOT_TOKEN = "7891234567:AAF..."

# ✅ GOOD - in .env (gitignored)
BOT_TOKEN=7891234567:AAF...
```

---

## 🤖 AI Assistant Behavior Rules

### 1. **Always Ask Before Destructive Actions**
- Before deleting files
- Before dropping database tables
- Before modifying production configs

### 2. **Provide Context in Commits**
```bash
# ✅ GOOD
git commit -m "feat: Add NFT minting service with TON integration

- Implement NFT metadata generation
- Add IPFS upload for images
- Create mint transaction tracking
- Add tests for minting flow"

# ❌ BAD
git commit -m "updates"
```

### 3. **Run Tests Before Committing**
```bash
# Always run before commit
pytest tests/ -v
ruff check .
mypy app/
```

### 4. **Explain Complex Decisions**
When implementing complex logic, add comments:
```python
# Calculate quiz result based on weighted scoring algorithm
# Each answer contributes to multiple result types with different weights
# The result type with highest cumulative weight wins
def calculate_quiz_result(answers: List[Answer]) -> str:
    scores = defaultdict(int)
    for answer in answers:
        for result_type, weight in answer.weights.items():
            scores[result_type] += weight
    return max(scores, key=scores.get)
```

### 5. **Use Logging Appropriately**
```python
from loguru import logger

# ✅ GOOD: Structured logging
logger.info(
    "User completed quiz",
    user_id=user_id,
    quiz_id=quiz_id,
    score=score,
    result_type=result_type
)

logger.error(
    "NFT minting failed",
    user_id=user_id,
    error=str(e),
    exc_info=True
)

# ❌ BAD
print(f"User {user_id} completed quiz")  # Don't use print
logger.info("Error occurred")  # No context
```

---

## 📋 Checklist Before Each Commit

- [ ] Code follows type hints standards
- [ ] All functions have docstrings
- [ ] Error handling is comprehensive
- [ ] Tests are written and passing
- [ ] No secrets in code
- [ ] Logging is appropriate
- [ ] Code is formatted (ruff format)
- [ ] Linting passes (ruff check)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated if needed

---

## 🎓 Learning Resources

- [Aiogram 3 Documentation](https://docs.aiogram.dev/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [TON Documentation](https://docs.ton.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

**Remember: Quality over speed. Write code that future you will thank you for.**
