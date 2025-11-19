"""Tests for payment service."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.result import QuizResult
from app.models.user import User
from app.services.payment_service import payment_service


@pytest_asyncio.fixture
async def test_quiz(db_session: AsyncSession, admin_user: User) -> Quiz:
    """Create a test quiz.

    Args:
        db_session: Database session.
        admin_user: Admin user fixture.

    Returns:
        Quiz: Test quiz instance.
    """
    quiz = Quiz(
        title="Test Quiz",
        description="A test quiz",
        is_active=True,
        created_by=admin_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    # Add question
    question = Question(
        quiz_id=quiz.id,
        text="Test question?",
        order_index=0,
    )
    db_session.add(question)
    await db_session.flush()

    # Add answers
    answer = Answer(
        question_id=question.id,
        text="Test answer",
        result_type="test_result",
        weight=1,
        order_index=0,
    )
    db_session.add(answer)

    # Add result type
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
    """Create a test quiz result.

    Args:
        db_session: Database session.
        test_user: Test user fixture.
        test_quiz: Test quiz fixture.

    Returns:
        QuizResult: Test quiz result instance.
    """
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


@pytest.mark.asyncio
async def test_create_mint_payment_success(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test successful payment creation."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )

    assert payment.id is not None
    assert payment.user_id == test_user.id
    assert payment.result_id == test_quiz_result.id
    assert payment.currency == "STARS"
    assert payment.status == "pending"
    assert payment.provider == "telegram_stars"
    assert payment.amount == 10  # Default STARS price


@pytest.mark.asyncio
async def test_create_mint_payment_returns_existing(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test that creating duplicate payment returns existing one."""
    # Create first payment
    payment1 = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Try to create second payment for same result
    payment2 = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )

    # Should return the same payment
    assert payment1.id == payment2.id


@pytest.mark.asyncio
async def test_create_mint_payment_invalid_provider(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test payment creation with invalid provider fails."""
    with pytest.raises(ValueError, match="Invalid payment provider"):
        await payment_service.create_mint_payment(
            session=db_session,
            user_id=test_user.id,
            result_id=test_quiz_result.id,
            provider="invalid_provider",
        )


@pytest.mark.asyncio
async def test_create_mint_payment_result_not_found(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """Test payment creation with non-existent result fails."""
    with pytest.raises(ValueError, match="Quiz result .* not found"):
        await payment_service.create_mint_payment(
            session=db_session,
            user_id=test_user.id,
            result_id=99999,  # Non-existent result
            provider="telegram_stars",
        )


@pytest.mark.asyncio
async def test_create_mint_payment_wrong_user(
    db_session: AsyncSession,
    admin_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test payment creation with wrong user fails."""
    with pytest.raises(ValueError, match="User does not own this quiz result"):
        await payment_service.create_mint_payment(
            session=db_session,
            user_id=admin_user.id,  # Different user
            result_id=test_quiz_result.id,
            provider="telegram_stars",
        )


@pytest.mark.asyncio
async def test_create_mint_payment_already_minted(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test payment creation for already minted NFT fails."""
    # Mark result as minted
    test_quiz_result.nft_minted = True
    await db_session.commit()

    with pytest.raises(ValueError, match="NFT already minted"):
        await payment_service.create_mint_payment(
            session=db_session,
            user_id=test_user.id,
            result_id=test_quiz_result.id,
            provider="telegram_stars",
        )


@pytest.mark.asyncio
async def test_create_stars_invoice(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test Telegram Stars invoice creation."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )

    # Create invoice
    invoice_data = payment_service.create_stars_invoice(
        payment=payment,
        title="Test Invoice",
        description="Test description",
    )

    assert invoice_data["title"] == "Test Invoice"
    assert invoice_data["description"] == "Test description"
    assert invoice_data["currency"] == "XTR"
    assert invoice_data["provider_token"] == ""
    assert f"nft_mint_{payment.id}_{test_quiz_result.id}" in invoice_data["payload"]
    assert len(invoice_data["prices"]) == 1
    assert invoice_data["prices"][0].amount == payment.amount


@pytest.mark.asyncio
async def test_handle_pre_checkout_valid(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test pre-checkout validation with valid payment."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Validate pre-checkout
    payload = f"nft_mint_{payment.id}_{test_quiz_result.id}"
    is_valid, error = await payment_service.handle_pre_checkout(
        session=db_session,
        invoice_payload=payload,
    )

    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_handle_pre_checkout_invalid_payload(
    db_session: AsyncSession,
) -> None:
    """Test pre-checkout validation with invalid payload."""
    is_valid, error = await payment_service.handle_pre_checkout(
        session=db_session,
        invoice_payload="invalid_payload",
    )

    assert is_valid is False
    assert error == "Invalid invoice payload"


@pytest.mark.asyncio
async def test_handle_pre_checkout_payment_not_found(
    db_session: AsyncSession,
) -> None:
    """Test pre-checkout validation with non-existent payment."""
    is_valid, error = await payment_service.handle_pre_checkout(
        session=db_session,
        invoice_payload="nft_mint_99999_1",
    )

    assert is_valid is False
    assert error == "Payment not found"


@pytest.mark.asyncio
async def test_handle_successful_payment(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test handling successful payment."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Handle successful payment
    payload = f"nft_mint_{payment.id}_{test_quiz_result.id}"
    updated_payment = await payment_service.handle_successful_payment(
        session=db_session,
        invoice_payload=payload,
        telegram_payment_charge_id="tg_12345",
        provider_payment_charge_id="prov_67890",
    )

    assert updated_payment.status == "paid"
    assert updated_payment.telegram_payment_charge_id == "tg_12345"
    assert updated_payment.provider_payment_id == "prov_67890"
    assert updated_payment.paid_at is not None


@pytest.mark.asyncio
async def test_handle_successful_payment_idempotency(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test that handling duplicate payment webhooks is idempotent."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Handle successful payment first time
    payload = f"nft_mint_{payment.id}_{test_quiz_result.id}"
    payment1 = await payment_service.handle_successful_payment(
        session=db_session,
        invoice_payload=payload,
        telegram_payment_charge_id="tg_12345",
        provider_payment_charge_id="prov_67890",
    )
    await db_session.commit()
    first_paid_at = payment1.paid_at

    # Handle duplicate webhook
    payment2 = await payment_service.handle_successful_payment(
        session=db_session,
        invoice_payload=payload,
        telegram_payment_charge_id="tg_12345",
        provider_payment_charge_id="prov_67890",
    )

    # Timestamp should not change
    assert payment2.paid_at == first_paid_at
    assert payment2.status == "paid"


@pytest.mark.asyncio
async def test_mark_payment_failed(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test marking payment as failed."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Mark as failed
    await payment_service.mark_payment_failed(
        session=db_session,
        payment_id=payment.id,
        reason="Test failure",
    )
    await db_session.commit()

    # Verify
    await db_session.refresh(payment)
    assert payment.status == "failed"


@pytest.mark.asyncio
async def test_refund_payment(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test refunding a paid payment."""
    # Create and pay
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    payment.status = "paid"
    await db_session.commit()

    # Refund
    refunded_payment = await payment_service.refund_payment(
        session=db_session,
        payment_id=payment.id,
    )

    assert refunded_payment.status == "refunded"


@pytest.mark.asyncio
async def test_refund_payment_not_paid(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test that refunding non-paid payment fails."""
    # Create payment (pending)
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Try to refund
    with pytest.raises(ValueError, match="Cannot refund payment"):
        await payment_service.refund_payment(
            session=db_session,
            payment_id=payment.id,
        )


@pytest.mark.asyncio
async def test_get_user_payments(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test getting user's payments."""
    # Create multiple payments
    payment1 = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    payment1.status = "paid"
    await db_session.commit()

    # Get payments
    payments = await payment_service.get_user_payments(
        session=db_session,
        user_id=test_user.id,
    )

    assert len(payments) == 1
    assert payments[0].id == payment1.id


@pytest.mark.asyncio
async def test_get_user_payments_filtered_by_status(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test getting user's payments filtered by status."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Get pending payments
    pending_payments = await payment_service.get_user_payments(
        session=db_session,
        user_id=test_user.id,
        status="pending",
    )

    assert len(pending_payments) == 1
    assert pending_payments[0].status == "pending"

    # Get paid payments (should be empty)
    paid_payments = await payment_service.get_user_payments(
        session=db_session,
        user_id=test_user.id,
        status="paid",
    )

    assert len(paid_payments) == 0


@pytest.mark.asyncio
async def test_get_payment_by_result(
    db_session: AsyncSession,
    test_user: User,
    test_quiz_result: QuizResult,
) -> None:
    """Test getting payment by result ID."""
    # Create payment
    payment = await payment_service.create_mint_payment(
        session=db_session,
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        provider="telegram_stars",
    )
    await db_session.commit()

    # Get by result
    found_payment = await payment_service.get_payment_by_result(
        session=db_session,
        result_id=test_quiz_result.id,
    )

    assert found_payment is not None
    assert found_payment.id == payment.id
