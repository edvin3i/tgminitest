"""Quiz result and NFT-related models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.quiz import Quiz
    from app.models.user import User


class QuizResult(Base, TimestampMixin):
    """QuizResult model storing user quiz completion results."""

    __tablename__ = "quiz_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answers_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    nft_minted: Mapped[bool] = mapped_column(default=False, nullable=False)
    nft_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quiz_results")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="quiz_results")
    mint_transaction: Mapped["MintTransaction | None"] = relationship(
        "MintTransaction",
        back_populates="result",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of QuizResult."""
        return (
            f"<QuizResult(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id}, "
            f"result_type={self.result_type}, nft_minted={self.nft_minted})>"
        )


class MintTransaction(Base, TimestampMixin):
    """MintTransaction model tracking NFT minting operations."""

    __tablename__ = "mint_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nft_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, processing, completed, failed
    metadata_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    result: Mapped["QuizResult"] = relationship("QuizResult", back_populates="mint_transaction")
    user: Mapped["User"] = relationship("User", back_populates="mint_transactions")

    def __repr__(self) -> str:
        """String representation of MintTransaction."""
        return (
            f"<MintTransaction(id={self.id}, result_id={self.result_id}, "
            f"status={self.status}, nft_address={self.nft_address})>"
        )


class NFTMetadata(Base, TimestampMixin):
    """NFTMetadata model storing NFT metadata templates for quiz results."""

    __tablename__ = "nft_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    attributes_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="nft_metadata")

    def __repr__(self) -> str:
        """String representation of NFTMetadata."""
        return (
            f"<NFTMetadata(id={self.id}, quiz_id={self.quiz_id}, "
            f"result_type={self.result_type}, name={self.name})>"
        )
