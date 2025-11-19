"""Quiz API endpoints."""


from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy import func, select

from app.api.dependencies import CurrentAdminUser, CurrentUser
from app.db.database import DBSession
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.schemas.quiz import (
    QuizCreate,
    QuizDetailResponse,
    QuizListResponse,
    QuizResultResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpdate,
)
from app.services.quiz_service import (
    calculate_result,
    get_quiz_by_id,
    get_result_type_info,
    get_user_quiz_results,
    save_quiz_result,
)

router = APIRouter()


@router.get("/", response_model=list[QuizListResponse])
async def list_quizzes(
    db: DBSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
) -> list[QuizListResponse]:
    """Get list of quizzes.

    Args:
        db: Database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        active_only: Only return active quizzes.

    Returns:
        List of quizzes.
    """
    query = select(Quiz).offset(skip).limit(limit)

    if active_only:
        query = query.where(Quiz.is_active == True)  # noqa: E712

    result = await db.execute(query)
    quizzes = result.scalars().all()

    # Count questions for each quiz
    quiz_list = []
    for quiz in quizzes:
        question_count_query = select(func.count(Question.id)).where(
            Question.quiz_id == quiz.id
        )
        question_count_result = await db.execute(question_count_query)
        question_count = question_count_result.scalar() or 0

        quiz_list.append(
            QuizListResponse(
                id=quiz.id,
                title=quiz.title,
                description=quiz.description,
                image_url=quiz.image_url,
                is_active=quiz.is_active,
                created_at=quiz.created_at,
                question_count=question_count,
            )
        )

    return quiz_list


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz(quiz_id: int) -> QuizDetailResponse:
    """Get quiz details by ID.

    Args:
        quiz_id: Quiz ID.

    Returns:
        Detailed quiz information.

    Raises:
        HTTPException: If quiz not found.
    """
    quiz = await get_quiz_by_id(quiz_id)

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz {quiz_id} not found",
        )

    return QuizDetailResponse.model_validate(quiz)


@router.post("/", response_model=QuizDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    db: DBSession,
    current_admin: CurrentAdminUser,
) -> QuizDetailResponse:
    """Create a new quiz (admin only).

    Args:
        quiz_data: Quiz creation data.
        db: Database session.
        current_admin: Current admin user.

    Returns:
        Created quiz.
    """
    try:
        # Create quiz
        quiz = Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            image_url=quiz_data.image_url,
            is_active=True,
            created_by=current_admin.id,
        )
        db.add(quiz)
        await db.flush()

        # Create result types
        for rt_data in quiz_data.result_types:
            result_type = ResultType(
                quiz_id=quiz.id,
                type_key=rt_data.type_key,
                title=rt_data.title,
                description=rt_data.description,
                image_url=rt_data.image_url,
            )
            db.add(result_type)

        # Create questions and answers
        for q_data in quiz_data.questions:
            question = Question(
                quiz_id=quiz.id,
                text=q_data.text,
                order_index=q_data.order_index,
            )
            db.add(question)
            await db.flush()

            for a_data in q_data.answers:
                answer = Answer(
                    question_id=question.id,
                    text=a_data.text,
                    result_type=a_data.result_type,
                    weight=a_data.weight,
                    order_index=a_data.order_index,
                )
                db.add(answer)

        await db.commit()
        await db.refresh(quiz)

        logger.info(f"Quiz {quiz.id} created by admin {current_admin.id}")

        # Load complete quiz data
        complete_quiz = await get_quiz_by_id(quiz.id)
        if not complete_quiz:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load created quiz",
            )

        return QuizDetailResponse.model_validate(complete_quiz)

    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quiz",
        ) from e


@router.patch("/{quiz_id}", response_model=QuizDetailResponse)
async def update_quiz(
    quiz_id: int,
    quiz_data: QuizUpdate,
    db: DBSession,
    current_admin: CurrentAdminUser,
) -> QuizDetailResponse:
    """Update quiz (admin only).

    Args:
        quiz_id: Quiz ID.
        quiz_data: Quiz update data.
        db: Database session.
        current_admin: Current admin user.

    Returns:
        Updated quiz.

    Raises:
        HTTPException: If quiz not found.
    """
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz {quiz_id} not found",
        )

    # Update fields
    update_data = quiz_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quiz, field, value)

    await db.commit()
    await db.refresh(quiz)

    logger.info(f"Quiz {quiz_id} updated by admin {current_admin.id}")

    # Load complete quiz data
    complete_quiz = await get_quiz_by_id(quiz_id)
    if not complete_quiz:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load updated quiz",
        )

    return QuizDetailResponse.model_validate(complete_quiz)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser,
) -> None:
    """Delete quiz (admin only).

    Args:
        quiz_id: Quiz ID.
        db: Database session.
        current_admin: Current admin user.

    Raises:
        HTTPException: If quiz not found.
    """
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz {quiz_id} not found",
        )

    await db.delete(quiz)
    await db.commit()

    logger.info(f"Quiz {quiz_id} deleted by admin {current_admin.id}")


@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmitRequest,
    current_user: CurrentUser,
) -> QuizSubmitResponse:
    """Submit quiz answers and get result.

    Args:
        quiz_id: Quiz ID.
        submission: Quiz submission with answer IDs.
        current_user: Current authenticated user.

    Returns:
        Quiz result.

    Raises:
        HTTPException: If quiz not found or submission invalid.
    """
    # Load quiz
    quiz = await get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz {quiz_id} not found",
        )

    try:
        # Calculate result
        result_type, score = await calculate_result(quiz, submission.answer_ids)

        # Save result
        quiz_result = await save_quiz_result(
            user_id=current_user.id,
            quiz_id=quiz_id,
            answer_ids=submission.answer_ids,
            result_type=result_type,
            score=score,
        )

        # Get result type info
        result_info = await get_result_type_info(quiz_id, result_type)

        return QuizSubmitResponse(
            result_id=quiz_result.id,
            result_type=result_type,
            result_title=result_info.title if result_info else result_type,
            result_description=result_info.description if result_info else "",
            score=score,
            nft_minted=False,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{quiz_id}/results", response_model=list[QuizResultResponse])
async def get_quiz_results(
    quiz_id: int,
    current_user: CurrentUser,
    limit: int = 10,
) -> list[QuizResultResponse]:
    """Get user's results for a specific quiz.

    Args:
        quiz_id: Quiz ID.
        current_user: Current authenticated user.
        limit: Maximum number of results.

    Returns:
        List of quiz results.
    """
    results = await get_user_quiz_results(current_user.id, limit=limit)

    # Filter by quiz_id
    filtered_results = [r for r in results if r.quiz_id == quiz_id]

    # Load quiz titles
    response_list = []
    for result in filtered_results:
        quiz = await get_quiz_by_id(result.quiz_id)
        response_list.append(
            QuizResultResponse(
                id=result.id,
                quiz_id=result.quiz_id,
                quiz_title=quiz.title if quiz else "Unknown Quiz",
                result_type=result.result_type,
                score=result.score,
                nft_minted=result.nft_minted,
                nft_address=result.nft_address,
                completed_at=result.completed_at,
            )
        )

    return response_list
