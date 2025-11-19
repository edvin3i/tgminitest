"""Pydantic schemas for User API."""

from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""

    total_quizzes_taken: int
    total_nfts_minted: int
    recent_results: list["QuizResultResponse"]  # Forward reference

    class Config:
        from_attributes = True


# Import to resolve forward reference (must be after class definition)
from app.schemas.quiz import QuizResultResponse  # noqa: E402

UserStatsResponse.model_rebuild()
