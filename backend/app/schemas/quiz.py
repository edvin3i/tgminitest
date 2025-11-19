"""Pydantic schemas for Quiz API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Answer schemas
class AnswerCreate(BaseModel):
    """Schema for creating an answer."""

    text: str = Field(..., min_length=1, max_length=512, description="Answer text")
    result_type: str = Field(..., min_length=1, max_length=100, description="Result type key")
    weight: int = Field(default=1, ge=1, le=10, description="Answer weight (1-10)")
    order_index: int = Field(..., ge=0, description="Display order")


class AnswerResponse(BaseModel):
    """Schema for answer response."""

    id: int
    text: str
    result_type: str
    weight: int
    order_index: int

    class Config:
        from_attributes = True


# Question schemas
class QuestionCreate(BaseModel):
    """Schema for creating a question."""

    text: str = Field(..., min_length=1, max_length=1000, description="Question text")
    order_index: int = Field(..., ge=0, description="Display order")
    answers: List[AnswerCreate] = Field(..., min_items=2, description="Answer options")


class QuestionResponse(BaseModel):
    """Schema for question response."""

    id: int
    text: str
    order_index: int
    answers: List[AnswerResponse]

    class Config:
        from_attributes = True


# Result Type schemas
class ResultTypeCreate(BaseModel):
    """Schema for creating a result type."""

    type_key: str = Field(..., min_length=1, max_length=100, description="Unique key")
    title: str = Field(..., min_length=1, max_length=255, description="Display title")
    description: str = Field(..., min_length=1, description="Result description")
    image_url: Optional[str] = Field(None, max_length=512, description="Result image URL")


class ResultTypeResponse(BaseModel):
    """Schema for result type response."""

    id: int
    type_key: str
    title: str
    description: str
    image_url: Optional[str]

    class Config:
        from_attributes = True


# Quiz schemas
class QuizCreate(BaseModel):
    """Schema for creating a quiz."""

    title: str = Field(..., min_length=1, max_length=255, description="Quiz title")
    description: str = Field(..., min_length=1, description="Quiz description")
    image_url: Optional[str] = Field(None, max_length=512, description="Quiz image URL")
    questions: List[QuestionCreate] = Field(
        ..., min_items=1, description="Quiz questions"
    )
    result_types: List[ResultTypeCreate] = Field(
        ..., min_items=2, description="Possible result types"
    )


class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, max_length=512)
    is_active: Optional[bool] = None


class QuizListResponse(BaseModel):
    """Schema for quiz list item."""

    id: int
    title: str
    description: str
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    question_count: int = Field(default=0, description="Number of questions")

    class Config:
        from_attributes = True


class QuizDetailResponse(BaseModel):
    """Schema for detailed quiz response."""

    id: int
    title: str
    description: str
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse]
    result_types: List[ResultTypeResponse]

    class Config:
        from_attributes = True


class QuizSubmitRequest(BaseModel):
    """Schema for submitting quiz answers."""

    answer_ids: List[int] = Field(..., min_items=1, description="Selected answer IDs")


class QuizSubmitResponse(BaseModel):
    """Schema for quiz submission result."""

    result_id: int
    result_type: str
    result_title: str
    result_description: str
    score: int
    nft_minted: bool


# Quiz Result schemas
class QuizResultResponse(BaseModel):
    """Schema for quiz result."""

    id: int
    quiz_id: int
    quiz_title: str
    result_type: str
    score: int
    nft_minted: bool
    nft_address: Optional[str]
    completed_at: datetime

    class Config:
        from_attributes = True
