"""Pydantic schemas package."""

from app.schemas.quiz import (
    AnswerCreate,
    AnswerResponse,
    QuestionCreate,
    QuestionResponse,
    QuizCreate,
    QuizDetailResponse,
    QuizListResponse,
    QuizResultResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpdate,
    ResultTypeCreate,
    ResultTypeResponse,
)
from app.schemas.user import UserResponse, UserStatsResponse

__all__ = [
    "AnswerCreate",
    "AnswerResponse",
    "QuestionCreate",
    "QuestionResponse",
    "ResultTypeCreate",
    "ResultTypeResponse",
    "QuizCreate",
    "QuizUpdate",
    "QuizListResponse",
    "QuizDetailResponse",
    "QuizSubmitRequest",
    "QuizSubmitResponse",
    "QuizResultResponse",
    "UserResponse",
    "UserStatsResponse",
]
