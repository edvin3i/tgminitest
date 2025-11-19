"""Tests for quiz API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.user import User


@pytest.fixture
async def api_client() -> AsyncClient:
    """Create async HTTP client for API testing.

    Returns:
        Async HTTP client.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers (mocked for testing).

    Args:
        test_user: Test user fixture.

    Returns:
        Auth headers dict.

    Note:
        In real tests, you'd generate valid Telegram initData.
        For now, we'll test the endpoints without auth.
    """
    return {}


@pytest.mark.asyncio
async def test_list_quizzes_empty(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test listing quizzes when database is empty."""
    response = await api_client.get("/api/v1/quizzes/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_quizzes(
    api_client: AsyncClient, db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test listing quizzes."""
    response = await api_client.get("/api/v1/quizzes/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_quiz.id
    assert data[0]["title"] == test_quiz.title
    assert data[0]["is_active"] is True


@pytest.mark.asyncio
async def test_get_quiz_detail(
    api_client: AsyncClient, db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test getting quiz details."""
    response = await api_client.get(f"/api/v1/quizzes/{test_quiz.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_quiz.id
    assert data["title"] == test_quiz.title
    assert "questions" in data
    assert "result_types" in data


@pytest.mark.asyncio
async def test_get_quiz_not_found(api_client: AsyncClient) -> None:
    """Test getting non-existent quiz."""
    response = await api_client.get("/api/v1/quizzes/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_quiz_validation(api_client: AsyncClient) -> None:
    """Test quiz creation with invalid data."""
    invalid_quiz = {
        "title": "",  # Empty title
        "description": "Test",
        "questions": [],  # No questions
        "result_types": [],  # No result types
    }

    response = await api_client.post("/api/v1/quizzes/", json=invalid_quiz)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_quizzes_pagination(
    api_client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    """Test quiz listing with pagination."""
    # Create multiple quizzes
    for i in range(5):
        quiz = Quiz(
            title=f"Quiz {i}",
            description=f"Description {i}",
            is_active=True,
            created_by=test_user.id,
        )
        db_session.add(quiz)

    await db_session.commit()

    # Test with limit
    response = await api_client.get("/api/v1/quizzes/?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Test with skip and limit
    response = await api_client.get("/api/v1/quizzes/?skip=2&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_quizzes_active_filter(
    api_client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    """Test filtering active/inactive quizzes."""
    # Create active quiz
    active_quiz = Quiz(
        title="Active Quiz",
        description="Active",
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(active_quiz)

    # Create inactive quiz
    inactive_quiz = Quiz(
        title="Inactive Quiz",
        description="Inactive",
        is_active=False,
        created_by=test_user.id,
    )
    db_session.add(inactive_quiz)

    await db_session.commit()

    # Test active_only=True (default)
    response = await api_client.get("/api/v1/quizzes/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_active"] is True

    # Test active_only=False
    response = await api_client.get("/api/v1/quizzes/?active_only=false")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
