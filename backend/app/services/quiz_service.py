"""Quiz service for managing quiz operations and result calculation."""

from collections import defaultdict
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.result import QuizResult


async def get_active_quizzes() -> list[Quiz]:
    """Get all active quizzes.

    Returns:
        List of active Quiz instances.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Quiz)
            .where(Quiz.is_active == True)  # noqa: E712
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars().all())


async def get_quiz_by_id(quiz_id: int) -> Quiz | None:
    """Get quiz by ID with all related data loaded.

    Args:
        quiz_id: Quiz database ID.

    Returns:
        Quiz instance with questions, answers, and result_types loaded,
        or None if not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Quiz)
            .options(
                selectinload(Quiz.questions).selectinload(Question.answers),
                selectinload(Quiz.result_types),
            )
            .where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()


async def calculate_result(quiz: Quiz, answer_ids: list[int]) -> tuple[str, int]:
    """Calculate quiz result based on weighted scoring algorithm.

    Each answer contributes to one or more result types with different weights.
    The result type with the highest cumulative weight wins.

    Args:
        quiz: Quiz instance with questions and answers loaded.
        answer_ids: List of answer IDs selected by the user.

    Returns:
        Tuple of (result_type, total_score).

    Raises:
        ValueError: If invalid answer IDs are provided.

    Example:
        ```python
        quiz = await get_quiz_by_id(1)
        result_type, score = await calculate_result(quiz, [1, 3, 5])
        # result_type = "gryffindor", score = 12
        ```
    """
    # Build a map of all valid answers for this quiz
    answer_map: dict[int, Answer] = {}
    for question in quiz.questions:
        for answer in question.answers:
            answer_map[answer.id] = answer

    # Validate all answer IDs belong to this quiz
    invalid_ids = set(answer_ids) - set(answer_map.keys())
    if invalid_ids:
        raise ValueError(f"Invalid answer IDs for this quiz: {invalid_ids}")

    # Calculate scores for each result type
    scores: dict[str, int] = defaultdict(int)
    for answer_id in answer_ids:
        answer = answer_map[answer_id]
        scores[answer.result_type] += answer.weight

    # Find the result type with the highest score
    if not scores:
        raise ValueError("No answers provided")

    result_type = max(scores, key=scores.get)  # type: ignore
    total_score = scores[result_type]

    logger.info(
        f"Calculated result for quiz {quiz.id}: {result_type} (score: {total_score})"
    )

    return result_type, total_score


async def save_quiz_result(
    user_id: int,
    quiz_id: int,
    answer_ids: list[int],
    result_type: str,
    score: int,
) -> QuizResult:
    """Save quiz result to database.

    Args:
        user_id: User database ID.
        quiz_id: Quiz database ID.
        answer_ids: List of answer IDs selected by the user.
        result_type: Calculated result type.
        score: Calculated score.

    Returns:
        Created QuizResult instance.

    Example:
        ```python
        result = await save_quiz_result(
            user_id=1,
            quiz_id=1,
            answer_ids=[1, 3, 5],
            result_type="gryffindor",
            score=12
        )
        ```
    """
    async with AsyncSessionLocal() as session:
        quiz_result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            answers_data={"answer_ids": answer_ids},
            result_type=result_type,
            score=score,
            nft_minted=False,
            completed_at=datetime.now(UTC),
        )
        session.add(quiz_result)
        await session.commit()
        await session.refresh(quiz_result)

        logger.info(
            f"Saved quiz result {quiz_result.id} for user {user_id}, "
            f"quiz {quiz_id}: {result_type}"
        )

        return quiz_result


async def get_user_quiz_results(user_id: int, limit: int = 10) -> list[QuizResult]:
    """Get user's quiz results.

    Args:
        user_id: User database ID.
        limit: Maximum number of results to return.

    Returns:
        List of QuizResult instances.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(QuizResult)
            .where(QuizResult.user_id == user_id)
            .order_by(QuizResult.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_result_type_info(quiz_id: int, result_type: str) -> ResultType | None:
    """Get result type information for a quiz.

    Args:
        quiz_id: Quiz database ID.
        result_type: Result type key.

    Returns:
        ResultType instance or None if not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ResultType)
            .where(ResultType.quiz_id == quiz_id, ResultType.type_key == result_type)
        )
        return result.scalar_one_or_none()
