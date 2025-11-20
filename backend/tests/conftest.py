"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Import all models to register them with Base.metadata
from app.models.base import Base
from app.models.quiz import Answer, Question, Quiz, ResultType  # noqa: F401
from app.models.result import MintTransaction, NFTMetadata, Payment, QuizResult  # noqa: F401
from app.models.user import User

# Test database URL - use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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


@pytest_asyncio.fixture
async def test_quiz(db_session: AsyncSession, test_user: User) -> Quiz:
    """Create a test quiz with questions and result types.

    Args:
        db_session: Database session.
        test_user: Test user who creates the quiz.

    Returns:
        Quiz: Test quiz instance with questions and result types.
    """
    # Create quiz
    quiz = Quiz(
        title="Test Quiz",
        description="Test quiz description",
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    # Create result types
    result_types = [
        ResultType(
            quiz_id=quiz.id,
            type_key="type_a",
            title="Type A",
            description="Result type A",
        ),
        ResultType(
            quiz_id=quiz.id,
            type_key="type_b",
            title="Type B",
            description="Result type B",
        ),
    ]
    db_session.add_all(result_types)
    await db_session.flush()

    # Create questions with answers
    question1 = Question(
        quiz_id=quiz.id,
        text="Question 1?",
        order_index=0,
    )
    db_session.add(question1)
    await db_session.flush()

    answers1 = [
        Answer(
            question_id=question1.id,
            text="Answer 1A",
            result_type="type_a",
            weight=1,
            order_index=0,
        ),
        Answer(
            question_id=question1.id,
            text="Answer 1B",
            result_type="type_b",
            weight=1,
            order_index=1,
        ),
    ]
    db_session.add_all(answers1)

    question2 = Question(
        quiz_id=quiz.id,
        text="Question 2?",
        order_index=1,
    )
    db_session.add(question2)
    await db_session.flush()

    answers2 = [
        Answer(
            question_id=question2.id,
            text="Answer 2A",
            result_type="type_a",
            weight=2,
            order_index=0,
        ),
        Answer(
            question_id=question2.id,
            text="Answer 2B",
            result_type="type_b",
            weight=2,
            order_index=1,
        ),
    ]
    db_session.add_all(answers2)

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


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
