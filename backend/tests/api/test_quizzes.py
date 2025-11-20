"""Tests for quiz API endpoints."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.quiz import Quiz
from app.models.user import User


def override_get_current_user(test_user: User):
    """Override get_current_user dependency for tests."""
    async def _get_current_user() -> User:
        return test_user
    return _get_current_user


def override_get_db(db_session: AsyncSession):
    """Override get_db dependency for tests."""
    async def _get_db():
        yield db_session
    return _get_db


def mock_async_session_local(db_session: AsyncSession):
    """Create a mock AsyncSessionLocal that returns test session."""
    @asynccontextmanager
    async def _session():
        yield db_session
    return _session


@pytest.fixture
async def api_client() -> AsyncClient:
    """Create async HTTP client for API testing.

    Returns:
        Async HTTP client.
    """
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
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
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await api_client.get("/api/v1/quizzes/")

        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_quizzes(
    api_client: AsyncClient, db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test listing quizzes."""
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await api_client.get("/api/v1/quizzes/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_quiz.id
        assert data[0]["title"] == test_quiz.title
        assert data[0]["is_active"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_quiz_detail(
    api_client: AsyncClient, db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test getting quiz details."""
    app.dependency_overrides[get_db] = override_get_db(db_session)

    # Patch AsyncSessionLocal used by quiz_service
    with patch("app.services.quiz_service.AsyncSessionLocal", mock_async_session_local(db_session)):
        try:
            response = await api_client.get(f"/api/v1/quizzes/{test_quiz.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == test_quiz.id
            assert data["title"] == test_quiz.title
            assert "questions" in data
            assert "result_types" in data
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_quiz_not_found(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test getting non-existent quiz."""
    app.dependency_overrides[get_db] = override_get_db(db_session)

    # Patch AsyncSessionLocal used by quiz_service
    with patch("app.services.quiz_service.AsyncSessionLocal", mock_async_session_local(db_session)):
        try:
            response = await api_client.get("/api/v1/quizzes/99999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_quiz_validation(api_client: AsyncClient, db_session: AsyncSession, admin_user: User) -> None:
    """Test quiz creation with invalid data."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = override_get_current_user(admin_user)

    try:
        invalid_quiz = {
            "title": "",  # Empty title
            "description": "Test",
            "questions": [],  # No questions
            "result_types": [],  # No result types
        }

        response = await api_client.post("/api/v1/quizzes/", json=invalid_quiz)

        assert response.status_code == 422  # Validation error
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_quizzes_pagination(
    api_client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    """Test quiz listing with pagination."""
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
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
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_quizzes_active_filter(
    api_client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    """Test filtering active/inactive quizzes."""
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
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
    finally:
        app.dependency_overrides.clear()
