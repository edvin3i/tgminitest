"""Quiz and related models."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.result import NFTMetadata, QuizResult
    from app.models.user import User


class Quiz(Base, TimestampMixin):
    """Quiz model representing a personality quiz."""

    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_quizzes")
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    result_types: Mapped[List["ResultType"]] = relationship(
        "ResultType", back_populates="quiz", cascade="all, delete-orphan"
    )
    quiz_results: Mapped[List["QuizResult"]] = relationship(
        "QuizResult", back_populates="quiz", cascade="all, delete-orphan"
    )
    nft_metadata: Mapped[List["NFTMetadata"]] = relationship(
        "NFTMetadata", back_populates="quiz", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Quiz."""
        return f"<Quiz(id={self.id}, title={self.title}, is_active={self.is_active})>"


class Question(Base, TimestampMixin):
    """Question model for quiz questions."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Answer.order_index",
    )

    def __repr__(self) -> str:
        """String representation of Question."""
        return f"<Question(id={self.id}, quiz_id={self.quiz_id}, order={self.order_index})>"


class Answer(Base, TimestampMixin):
    """Answer model for question answer options."""

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        """String representation of Answer."""
        return (
            f"<Answer(id={self.id}, question_id={self.question_id}, "
            f"result_type={self.result_type})>"
        )


class ResultType(Base, TimestampMixin):
    """ResultType model defining possible quiz result categories."""

    __tablename__ = "result_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="result_types")

    def __repr__(self) -> str:
        """String representation of ResultType."""
        return f"<ResultType(id={self.id}, quiz_id={self.quiz_id}, type_key={self.type_key})>"
