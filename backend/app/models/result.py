"""Quiz result and NFT-related models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
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
        default=lambda: datetime.now(UTC), nullable=False
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
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nft_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ipfs_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, uploading_image, uploading_metadata, minting, completed, failed
    metadata_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    result: Mapped["QuizResult"] = relationship("QuizResult", back_populates="mint_transaction")
    user: Mapped["User"] = relationship("User", back_populates="mint_transactions")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="mint_transaction")

    def __repr__(self) -> str:
        """String representation of MintTransaction."""
        return (
            f"<MintTransaction(id={self.id}, result_id={self.result_id}, "
            f"status={self.status}, nft_address={self.nft_address})>"
        )


class NFTMetadata(Base, TimestampMixin):
    """NFTMetadata model storing NFT metadata for minted quiz results."""

    __tablename__ = "nft_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    metadata_url: Mapped[str] = mapped_column(String(512), nullable=False)
    attributes: Mapped[list] = mapped_column(JSONB, nullable=False)

    # Relationships
    result: Mapped["QuizResult"] = relationship("QuizResult")

    def __repr__(self) -> str:
        """String representation of NFTMetadata."""
        return (
            f"<NFTMetadata(id={self.id}, result_id={self.result_id}, name={self.name})>"
        )


class Payment(Base, TimestampMixin):
    """Payment model tracking Telegram Stars and TON payments for NFT minting."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    result_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In smallest units
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # STARS, TON, USD
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, paid, failed, refunded
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # telegram_stars, ton_connect
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    result: Mapped["QuizResult"] = relationship("QuizResult")
    mint_transaction: Mapped["MintTransaction | None"] = relationship(
        "MintTransaction",
        back_populates="payment",
        uselist=False,
    )

    def __repr__(self) -> str:
        """String representation of Payment."""
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, currency={self.currency}, status={self.status})>"
        )
