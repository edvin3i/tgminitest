"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models import Base, User

# Test database URL
TEST_DATABASE_URL = (
    "postgresql+asyncpg://quizbot:changeme@localhost:5432/telegram_quiz_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session.

    Yields:
        Event loop instance.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[Any, None]:
    """Create async engine for tests.

    Yields:
        SQLAlchemy async engine.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests.

    Args:
        test_engine: Test database engine.

    Yields:
        AsyncSession: Database session.
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user.

    Args:
        db_session: Database session.

    Returns:
        User: Test user instance.
    """
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user.

    Args:
        db_session: Database session.

    Returns:
        User: Test admin user instance.
    """
    user = User(
        telegram_id=987654321,
        username="admin",
        first_name="Admin",
        last_name="User",
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def sample_quiz_data() -> dict[str, Any]:
    """Sample quiz data for testing.

    Returns:
        Dictionary with quiz data.
    """
    return {
        "title": "Hogwarts House Quiz",
        "description": "Find out which Hogwarts house you belong to!",
        "questions": [
            {
                "text": "What is your favorite color?",
                "order_index": 0,
                "answers": [
                    {"text": "Red", "result_type": "gryffindor", "weight": 1, "order_index": 0},
                    {"text": "Green", "result_type": "slytherin", "weight": 1, "order_index": 1},
                    {"text": "Blue", "result_type": "ravenclaw", "weight": 1, "order_index": 2},
                    {"text": "Yellow", "result_type": "hufflepuff", "weight": 1, "order_index": 3},
                ],
            },
            {
                "text": "What do you value most?",
                "order_index": 1,
                "answers": [
                    {"text": "Bravery", "result_type": "gryffindor", "weight": 2, "order_index": 0},
                    {"text": "Ambition", "result_type": "slytherin", "weight": 2, "order_index": 1},
                    {"text": "Wisdom", "result_type": "ravenclaw", "weight": 2, "order_index": 2},
                    {"text": "Loyalty", "result_type": "hufflepuff", "weight": 2, "order_index": 3},
                ],
            },
        ],
        "result_types": [
            {
                "type_key": "gryffindor",
                "title": "Gryffindor",
                "description": "You are brave and daring!",
            },
            {
                "type_key": "slytherin",
                "title": "Slytherin",
                "description": "You are ambitious and cunning!",
            },
            {
                "type_key": "ravenclaw",
                "title": "Ravenclaw",
                "description": "You are wise and creative!",
            },
            {
                "type_key": "hufflepuff",
                "title": "Hufflepuff",
                "description": "You are loyal and hardworking!",
            },
        ],
    }
