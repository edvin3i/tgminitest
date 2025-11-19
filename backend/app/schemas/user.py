"""Pydantic schemas for User API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""

    total_quizzes_taken: int
    total_nfts_minted: int
    recent_results: List["QuizResultResponse"]  # Forward reference

    class Config:
        from_attributes = True


# Import to resolve forward reference
from app.schemas.quiz import QuizResultResponse

UserStatsResponse.model_rebuild()
