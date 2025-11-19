"""Tests for NFT bot handlers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.nft import (
    _format_nft_collection_text,
    handle_pre_checkout,
    initiate_nft_mint,
    show_my_nfts,
)
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.result import QuizResult
from app.models.user import User


@pytest_asyncio.fixture
async def test_quiz(db_session: AsyncSession, admin_user: User) -> Quiz:
    """Create a test quiz."""
    quiz = Quiz(
        title="Test Quiz",
        description="A test quiz",
        is_active=True,
        created_by=admin_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    question = Question(
        quiz_id=quiz.id,
        text="Test question?",
        order_index=0,
    )
    db_session.add(question)
    await db_session.flush()

    answer = Answer(
        question_id=question.id,
        text="Test answer",
        result_type="test_result",
        weight=1,
        order_index=0,
    )
    db_session.add(answer)

    result_type = ResultType(
        quiz_id=quiz.id,
        type_key="test_result",
        title="Test Result",
        description="A test result",
    )
    db_session.add(result_type)

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest_asyncio.fixture
async def test_quiz_result(
    db_session: AsyncSession,
    test_user: User,
    test_quiz: Quiz,
) -> QuizResult:
    """Create a test quiz result."""
    quiz_result = QuizResult(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        answers_data={"1": 1},
        result_type="test_result",
        score=10,
        nft_minted=False,
    )
    db_session.add(quiz_result)
    await db_session.commit()
    await db_session.refresh(quiz_result)
    return quiz_result


def test_format_nft_collection_text_empty() -> None:
    """Test formatting empty NFT collection."""
    text = _format_nft_collection_text([])

    assert "You don't have any NFTs yet!" in text
    assert "/quiz" in text


def test_format_nft_collection_text_with_nfts() -> None:
    """Test formatting NFT collection with NFTs."""
    from datetime import UTC, datetime

    nfts = [
        {
            "nft_address": "EQD...test123",
            "transaction_hash": "tx_123",
            "minted_at": datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
            "result_id": 1,
            "metadata": {
                "name": "Test NFT",
                "description": "Test description",
                "image": "https://example.com/image.png",
                "attributes": [],
                "metadata_url": "https://example.com/metadata.json",
            },
        }
    ]

    text = _format_nft_collection_text(nfts)

    assert "You have 1 NFT(s)" in text
    assert "Test NFT" in text
    assert "EQD...test123" in text
    assert "2025-01-01 12:00" in text


@pytest.mark.asyncio
async def test_initiate_nft_mint_user_not_found() -> None:
    """Test initiating NFT mint when user not found."""
    # Create mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "mint_nft:1"
    callback.from_user = MagicMock(spec=TgUser)
    callback.from_user.id = 123456
    callback.message = MagicMock()  # Changed from None to MagicMock
    callback.answer = AsyncMock()  # Explicitly make it AsyncMock

    with patch("app.bot.handlers.nft.get_user_by_telegram_id", new=AsyncMock(return_value=None)):
        await initiate_nft_mint(callback)

    callback.answer.assert_called_once()
    assert "User not found" in str(callback.answer.call_args)


@pytest.mark.asyncio
async def test_initiate_nft_mint_success(
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test successful NFT mint initiation."""
    # Create mock callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = f"mint_nft:{test_quiz_result.id}"
    callback.from_user = MagicMock(spec=TgUser)
    callback.from_user.id = test_user.telegram_id
    callback.message = AsyncMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123456
    callback.message.bot = AsyncMock()
    callback.answer = AsyncMock()  # Explicitly make it AsyncMock

    with patch("app.bot.handlers.nft.get_user_by_telegram_id", new=AsyncMock(return_value=test_user)):
        with patch("app.bot.handlers.nft.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock payment creation
            mock_payment = MagicMock()
            mock_payment.id = 1
            mock_payment.amount = 10
            mock_payment.currency = "STARS"
            mock_payment.provider = "telegram_stars"

            with patch(
                "app.bot.handlers.nft.payment_service.create_mint_payment",
                new=AsyncMock(return_value=mock_payment),
            ):
                # Mock quiz result retrieval
                mock_db.get = AsyncMock(return_value=test_quiz_result)
                mock_db.refresh = AsyncMock()
                mock_db.commit = AsyncMock()

                with patch(
                    "app.bot.handlers.nft.payment_service.create_stars_invoice",
                    return_value={
                        "title": "Test",
                        "description": "Test",
                        "payload": "test_payload",
                        "provider_token": "",
                        "currency": "XTR",
                        "prices": [],
                    },
                ):
                    await initiate_nft_mint(callback)

    # Verify invoice was sent
    callback.message.bot.send_invoice.assert_called_once()
    callback.answer.assert_called_once()
    assert "invoice sent" in str(callback.answer.call_args).lower()


@pytest.mark.asyncio
async def test_handle_pre_checkout_valid(
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test pre-checkout with valid payment."""
    # Create mock pre-checkout query
    pre_checkout = AsyncMock(spec=PreCheckoutQuery)
    pre_checkout.invoice_payload = "nft_mint_1_1"
    pre_checkout.answer = AsyncMock()  # Explicitly make it AsyncMock

    with patch("app.bot.handlers.nft.AsyncSessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        with patch(
            "app.bot.handlers.nft.payment_service.handle_pre_checkout",
            new=AsyncMock(return_value=(True, None)),
        ):
            await handle_pre_checkout(pre_checkout)

    pre_checkout.answer.assert_called_once_with(ok=True)


@pytest.mark.asyncio
async def test_handle_pre_checkout_invalid(
) -> None:
    """Test pre-checkout with invalid payment."""
    # Create mock pre-checkout query
    pre_checkout = AsyncMock(spec=PreCheckoutQuery)
    pre_checkout.invoice_payload = "invalid_payload"
    pre_checkout.answer = AsyncMock()  # Explicitly make it AsyncMock

    with patch("app.bot.handlers.nft.AsyncSessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        with patch(
            "app.bot.handlers.nft.payment_service.handle_pre_checkout",
            new=AsyncMock(return_value=(False, "Payment not found")),
        ):
            await handle_pre_checkout(pre_checkout)

    pre_checkout.answer.assert_called_once()
    call_args = pre_checkout.answer.call_args
    assert call_args[1]["ok"] is False
    assert "Payment not found" in call_args[1]["error_message"]


@pytest.mark.asyncio
async def test_show_my_nfts_user_not_found() -> None:
    """Test showing NFTs when user not found."""
    # Create mock message
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = 123456
    message.answer = AsyncMock()

    with patch("app.bot.handlers.nft.get_user_by_telegram_id", new=AsyncMock(return_value=None)):
        await show_my_nfts(message)

    message.answer.assert_called_once()
    assert "User not found" in str(message.answer.call_args)


@pytest.mark.asyncio
async def test_show_my_nfts_empty_collection(
    test_user: User,
) -> None:
    """Test showing empty NFT collection."""
    # Create mock message
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = test_user.telegram_id
    message.answer = AsyncMock()

    with patch("app.bot.handlers.nft.get_user_by_telegram_id", new=AsyncMock(return_value=test_user)):
        with patch("app.bot.handlers.nft.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.bot.handlers.nft.nft_service.get_user_nfts",
                new=AsyncMock(return_value=[]),
            ):
                await show_my_nfts(message)

    message.answer.assert_called_once()
    call_text = str(message.answer.call_args)
    assert "don't have any NFTs yet" in call_text


@pytest.mark.asyncio
async def test_show_my_nfts_with_nfts(
    test_user: User,
) -> None:
    """Test showing NFT collection with NFTs."""
    from datetime import UTC, datetime

    # Create mock message
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = test_user.telegram_id
    message.answer = AsyncMock()

    nfts = [
        {
            "nft_address": "EQD...test123",
            "transaction_hash": "tx_123",
            "minted_at": datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
            "result_id": 1,
            "metadata": {
                "name": "Test NFT",
                "description": "Test",
                "image": "https://example.com/image.png",
                "attributes": [],
                "metadata_url": "https://example.com/metadata.json",
            },
        }
    ]

    with patch("app.bot.handlers.nft.get_user_by_telegram_id", new=AsyncMock(return_value=test_user)):
        with patch("app.bot.handlers.nft.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.bot.handlers.nft.nft_service.get_user_nfts",
                new=AsyncMock(return_value=nfts),
            ):
                await show_my_nfts(message)

    message.answer.assert_called_once()
    call_text = str(message.answer.call_args)
    assert "You have 1 NFT(s)" in call_text
    assert "Test NFT" in call_text
