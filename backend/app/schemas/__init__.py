"""Pydantic schemas package."""

from app.schemas.nft import (
    MintConfirmRequest,
    MintConfirmResponse,
    NFTMetadataResponse,
    NFTMintRequest,
    NFTMintStatusResponse,
    PaymentInvoiceResponse,
    UserNFTResponse,
)
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
    "MintConfirmRequest",
    "MintConfirmResponse",
    "NFTMetadataResponse",
    "NFTMintRequest",
    "NFTMintStatusResponse",
    "PaymentInvoiceResponse",
    "QuestionCreate",
    "QuestionResponse",
    "QuizCreate",
    "QuizDetailResponse",
    "QuizListResponse",
    "QuizResultResponse",
    "QuizSubmitRequest",
    "QuizSubmitResponse",
    "QuizUpdate",
    "ResultTypeCreate",
    "ResultTypeResponse",
    "UserNFTResponse",
    "UserResponse",
    "UserStatsResponse",
]
