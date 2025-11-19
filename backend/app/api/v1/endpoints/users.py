"""User API endpoints."""


from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser
from app.db.database import DBSession
from app.models.result import QuizResult
from app.schemas.quiz import QuizResultResponse
from app.schemas.user import UserResponse, UserStatsResponse
from app.services.quiz_service import get_quiz_by_id, get_user_quiz_results

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser) -> UserResponse:
    """Get current user profile.

    Args:
        current_user: Current authenticated user.

    Returns:
        User profile.
    """
    return UserResponse.model_validate(current_user)


@router.get("/me/results", response_model=list[QuizResultResponse])
async def get_my_quiz_results(
    current_user: CurrentUser,
    limit: int = 20,
) -> list[QuizResultResponse]:
    """Get current user's quiz results.

    Args:
        current_user: Current authenticated user.
        limit: Maximum number of results.

    Returns:
        List of quiz results.
    """
    results = await get_user_quiz_results(current_user.id, limit=limit)

    # Load quiz titles
    response_list = []
    for result in results:
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


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: CurrentUser,
    db: DBSession,
) -> UserStatsResponse:
    """Get current user's statistics.

    Args:
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        User statistics.
    """
    # Count total quizzes taken
    quiz_count_query = select(func.count(QuizResult.id)).where(
        QuizResult.user_id == current_user.id
    )
    quiz_count_result = await db.execute(quiz_count_query)
    total_quizzes = quiz_count_result.scalar() or 0

    # Count NFTs minted
    nft_count_query = select(func.count(QuizResult.id)).where(
        QuizResult.user_id == current_user.id,
        QuizResult.nft_minted == True,  # noqa: E712
    )
    nft_count_result = await db.execute(nft_count_query)
    total_nfts = nft_count_result.scalar() or 0

    # Get recent results
    results = await get_user_quiz_results(current_user.id, limit=5)

    # Load quiz titles
    recent_results = []
    for result in results:
        quiz = await get_quiz_by_id(result.quiz_id)
        recent_results.append(
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

    return UserStatsResponse(
        total_quizzes_taken=total_quizzes,
        total_nfts_minted=total_nfts,
        recent_results=recent_results,
    )
