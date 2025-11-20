"""Tests for quiz service."""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.user import User
from app.services.quiz_service import (
    calculate_result,
    get_active_quizzes,
    get_quiz_by_id,
    get_result_type_info,
    save_quiz_result,
)


def mock_async_session_local(db_session: AsyncSession):
    """Create a mock AsyncSessionLocal that returns test session."""
    @asynccontextmanager
    async def _session():
        yield db_session
    return _session


@pytest.fixture(autouse=True)
def patch_async_session(db_session: AsyncSession):
    """Auto-patch AsyncSessionLocal for all tests in this module."""
    with patch("app.services.quiz_service.AsyncSessionLocal", mock_async_session_local(db_session)):
        yield


@pytest.fixture
async def test_quiz(db_session: AsyncSession, test_user: User) -> Quiz:
    """Create a test quiz with questions and answers.

    Args:
        db_session: Database session.
        test_user: Test user.

    Returns:
        Created quiz instance.
    """
    quiz = Quiz(
        title="Test Quiz",
        description="A test quiz",
        is_active=True,
        created_by=test_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    # Create result types
    for house in ["gryffindor", "slytherin"]:
        result_type = ResultType(
            quiz_id=quiz.id,
            type_key=house,
            title=house.capitalize(),
            description=f"You are {house}!",
        )
        db_session.add(result_type)

    # Create questions and answers
    for i in range(3):
        question = Question(
            quiz_id=quiz.id, text=f"Question {i+1}?", order_index=i
        )
        db_session.add(question)
        await db_session.flush()

        # Add two answers per question
        answer1 = Answer(
            question_id=question.id,
            text="Answer A",
            result_type="gryffindor",
            weight=2,
            order_index=0,
        )
        answer2 = Answer(
            question_id=question.id,
            text="Answer B",
            result_type="slytherin",
            weight=2,
            order_index=1,
        )
        db_session.add(answer1)
        db_session.add(answer2)

    await db_session.commit()
    await db_session.refresh(quiz)

    return quiz


@pytest.mark.asyncio
async def test_get_active_quizzes(db_session: AsyncSession, test_quiz: Quiz) -> None:
    """Test getting active quizzes."""
    quizzes = await get_active_quizzes()

    assert len(quizzes) == 1
    assert quizzes[0].id == test_quiz.id
    assert quizzes[0].title == "Test Quiz"
    assert quizzes[0].is_active is True


@pytest.mark.asyncio
async def test_get_active_quizzes_filters_inactive(
    db_session: AsyncSession, test_user: User
) -> None:
    """Test that inactive quizzes are filtered out."""
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

    quizzes = await get_active_quizzes()

    assert len(quizzes) == 1
    assert quizzes[0].id == active_quiz.id


@pytest.mark.asyncio
async def test_get_quiz_by_id(db_session: AsyncSession, test_quiz: Quiz) -> None:
    """Test getting quiz by ID with related data."""
    quiz = await get_quiz_by_id(test_quiz.id)

    assert quiz is not None
    assert quiz.id == test_quiz.id
    assert quiz.title == "Test Quiz"
    assert len(quiz.questions) == 3
    assert len(quiz.questions[0].answers) == 2
    assert len(quiz.result_types) == 2


@pytest.mark.asyncio
async def test_get_quiz_by_id_not_found(db_session: AsyncSession) -> None:
    """Test getting non-existent quiz."""
    quiz = await get_quiz_by_id(99999)

    assert quiz is None


@pytest.mark.asyncio
async def test_calculate_result(db_session: AsyncSession, test_quiz: Quiz) -> None:
    """Test result calculation with weighted scoring."""
    # Reload quiz with relationships
    quiz = await get_quiz_by_id(test_quiz.id)
    assert quiz is not None

    # Get all "gryffindor" answers (3 questions * 2 weight each = 6 total)
    answer_ids = [
        quiz.questions[0].answers[0].id,  # gryffindor
        quiz.questions[1].answers[0].id,  # gryffindor
        quiz.questions[2].answers[0].id,  # gryffindor
    ]

    result_type, score = await calculate_result(quiz, answer_ids)

    assert result_type == "gryffindor"
    assert score == 6  # 3 questions * 2 weight


@pytest.mark.asyncio
async def test_calculate_result_mixed_answers(
    db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test result calculation with mixed answers."""
    quiz = await get_quiz_by_id(test_quiz.id)
    assert quiz is not None

    # Mix of answers: 2 gryffindor (4 points), 1 slytherin (2 points)
    answer_ids = [
        quiz.questions[0].answers[0].id,  # gryffindor (2)
        quiz.questions[1].answers[0].id,  # gryffindor (2)
        quiz.questions[2].answers[1].id,  # slytherin (2)
    ]

    result_type, score = await calculate_result(quiz, answer_ids)

    assert result_type == "gryffindor"  # Higher score
    assert score == 4


@pytest.mark.asyncio
async def test_calculate_result_invalid_answer_ids(
    db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test result calculation with invalid answer IDs."""
    quiz = await get_quiz_by_id(test_quiz.id)
    assert quiz is not None

    # Use invalid answer IDs
    answer_ids = [99999, 99998, 99997]

    with pytest.raises(ValueError, match="Invalid answer IDs"):
        await calculate_result(quiz, answer_ids)


@pytest.mark.asyncio
async def test_calculate_result_empty_answers(
    db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test result calculation with no answers."""
    quiz = await get_quiz_by_id(test_quiz.id)
    assert quiz is not None

    with pytest.raises(ValueError, match="No answers provided"):
        await calculate_result(quiz, [])


@pytest.mark.asyncio
async def test_save_quiz_result(
    db_session: AsyncSession, test_user: User, test_quiz: Quiz
) -> None:
    """Test saving quiz result."""
    answer_ids = [1, 2, 3]

    result = await save_quiz_result(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        answer_ids=answer_ids,
        result_type="gryffindor",
        score=10,
    )

    assert result.id is not None
    assert result.user_id == test_user.id
    assert result.quiz_id == test_quiz.id
    assert result.result_type == "gryffindor"
    assert result.score == 10
    assert result.answers_data == {"answer_ids": answer_ids}
    assert result.nft_minted is False
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_get_result_type_info(
    db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test getting result type information."""
    result_info = await get_result_type_info(test_quiz.id, "gryffindor")

    assert result_info is not None
    assert result_info.type_key == "gryffindor"
    assert result_info.title == "Gryffindor"
    assert result_info.description == "You are gryffindor!"


@pytest.mark.asyncio
async def test_get_result_type_info_not_found(
    db_session: AsyncSession, test_quiz: Quiz
) -> None:
    """Test getting non-existent result type."""
    result_info = await get_result_type_info(test_quiz.id, "nonexistent")

    assert result_info is None
