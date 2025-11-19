"""Payment service for handling Telegram Stars and TON payments."""

from datetime import UTC, datetime
from typing import Any

from aiogram.types import LabeledPrice
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.result import Payment, QuizResult


class PaymentService:
    """Service for handling payments for NFT minting."""

    def __init__(self) -> None:
        """Initialize payment service."""
        self.stars_enabled = settings.STARS_ENABLED
        self.ton_enabled = settings.TON_PAYMENT_ENABLED
        self.stars_price = settings.NFT_MINT_PRICE_STARS
        self.ton_price = settings.NFT_MINT_PRICE_TON

    async def create_mint_payment(
        self,
        session: AsyncSession,
        user_id: int,
        result_id: int,
        provider: str = "telegram_stars",
    ) -> Payment:
        """Create a payment record for NFT minting.

        Args:
            session: Database session.
            user_id: User ID.
            result_id: Quiz result ID.
            provider: Payment provider (telegram_stars or ton_connect).

        Returns:
            Created Payment record.

        Raises:
            ValueError: If provider is invalid or result doesn't exist.
        """
        # Validate provider
        if provider not in ["telegram_stars", "ton_connect"]:
            raise ValueError(f"Invalid payment provider: {provider}")

        if provider == "telegram_stars" and not self.stars_enabled:
            raise ValueError("Telegram Stars payments are disabled")

        if provider == "ton_connect" and not self.ton_enabled:
            raise ValueError("TON payments are disabled")

        # Check if result exists
        result = await session.get(QuizResult, result_id)
        if not result:
            raise ValueError(f"Quiz result {result_id} not found")

        if result.user_id != user_id:
            raise ValueError("User does not own this quiz result")

        if result.nft_minted:
            raise ValueError("NFT already minted for this result")

        # Check if payment already exists
        stmt = select(Payment).where(
            Payment.result_id == result_id,
            Payment.status.in_(["pending", "paid"]),
        )
        existing_payment = await session.scalar(stmt)
        if existing_payment:
            logger.info(
                f"Returning existing payment {existing_payment.id} for result {result_id}"
            )
            return existing_payment

        # Determine amount based on provider
        if provider == "telegram_stars":
            amount = self.stars_price
            currency = "STARS"
        else:  # ton_connect
            # Convert TON to nanotons (1 TON = 1_000_000_000 nanotons)
            amount = int(self.ton_price * 1_000_000_000)
            currency = "TON"

        # Create payment record
        payment = Payment(
            user_id=user_id,
            result_id=result_id,
            amount=amount,
            currency=currency,
            status="pending",
            provider=provider,
        )

        session.add(payment)

        try:
            await session.flush()
            logger.info(
                f"Created payment {payment.id} for user {user_id}, "
                f"result {result_id}, amount {amount} {currency}"
            )
            return payment
        except IntegrityError:
            # Race condition: another request created payment first
            # Rollback and query for the existing payment
            await session.rollback()
            stmt = select(Payment).where(
                Payment.result_id == result_id,
                Payment.status.in_(["pending", "paid"]),
            )
            existing_payment = await session.scalar(stmt)
            if existing_payment:
                logger.info(
                    f"Race condition detected: returning existing payment "
                    f"{existing_payment.id} for result {result_id}"
                )
                return existing_payment  # type: ignore[no-any-return]
            # If we still don't find it, re-raise
            raise

    def create_stars_invoice(
        self,
        payment: Payment,
        title: str,
        description: str,
    ) -> dict[str, Any]:
        """Create Telegram Stars invoice data.

        Args:
            payment: Payment record.
            title: Invoice title.
            description: Invoice description.

        Returns:
            Dictionary with invoice data for aiogram.

        Raises:
            ValueError: If payment is not for Telegram Stars.
        """
        if payment.currency != "STARS":
            raise ValueError("Payment is not for Telegram Stars")

        # Telegram Stars invoice structure for aiogram
        return {
            "title": title,
            "description": description,
            "payload": f"nft_mint_{payment.id}_{payment.result_id}",
            "provider_token": "",  # Empty for Stars
            "currency": "XTR",  # Telegram Stars currency code
            "prices": [
                LabeledPrice(
                    label="NFT Minting Fee",
                    amount=payment.amount,
                )
            ],
        }


    async def handle_pre_checkout(
        self,
        session: AsyncSession,
        invoice_payload: str,
    ) -> tuple[bool, str | None]:
        """Handle pre-checkout query validation.

        Args:
            session: Database session.
            invoice_payload: Invoice payload from pre-checkout query.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            # Parse payload: nft_mint_{payment_id}_{result_id}
            parts = invoice_payload.split("_")
            if len(parts) != 4 or parts[0] != "nft" or parts[1] != "mint":
                return False, "Invalid invoice payload"

            payment_id = int(parts[2])
            result_id = int(parts[3])

            # Get payment
            payment = await session.get(Payment, payment_id)
            if not payment:
                return False, "Payment not found"

            if payment.result_id != result_id:
                return False, "Payment result mismatch"

            if payment.status != "pending":
                return False, f"Payment status is {payment.status}, expected pending"

            # Check if result is still valid for minting
            result = await session.get(QuizResult, result_id)
            if not result:
                return False, "Quiz result not found"

            if result.nft_minted:
                return False, "NFT already minted for this result"

            logger.info(
                f"Pre-checkout validated for payment {payment_id}, result {result_id}"
            )
            return True, None

        except Exception as e:
            logger.exception(f"Error in pre-checkout validation: {e}")
            return False, "Validation error"

    async def handle_successful_payment(
        self,
        session: AsyncSession,
        invoice_payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
    ) -> Payment:
        """Handle successful payment callback.

        Args:
            session: Database session.
            invoice_payload: Invoice payload from successful payment.
            telegram_payment_charge_id: Telegram payment charge ID.
            provider_payment_charge_id: Provider payment charge ID.

        Returns:
            Updated Payment record.

        Raises:
            ValueError: If payment validation fails.
        """
        try:
            # Parse payload
            parts = invoice_payload.split("_")
            if len(parts) != 4 or parts[0] != "nft" or parts[1] != "mint":
                raise ValueError("Invalid invoice payload")

            payment_id = int(parts[2])

            # Get payment
            payment = await session.get(Payment, payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")

            if payment.status == "paid":
                logger.warning(f"Payment {payment_id} already marked as paid")
                return payment

            # Update payment status
            payment.status = "paid"
            payment.telegram_payment_charge_id = telegram_payment_charge_id
            payment.provider_payment_id = provider_payment_charge_id
            # Only set paid_at if not already set (for idempotency)
            if payment.paid_at is None:
                payment.paid_at = datetime.now(UTC)

            await session.flush()

            logger.info(
                f"Payment {payment_id} marked as paid "
                f"(telegram_charge: {telegram_payment_charge_id})"
            )

            return payment

        except Exception as e:
            logger.exception(f"Error handling successful payment: {e}")
            raise

    async def mark_payment_failed(
        self,
        session: AsyncSession,
        payment_id: int,
        reason: str,
    ) -> None:
        """Mark payment as failed.

        Args:
            session: Database session.
            payment_id: Payment ID.
            reason: Failure reason.
        """
        payment = await session.get(Payment, payment_id)
        if not payment:
            logger.warning(f"Payment {payment_id} not found for failure marking")
            return

        payment.status = "failed"
        await session.flush()

        logger.info(f"Payment {payment_id} marked as failed: {reason}")

    async def refund_payment(
        self,
        session: AsyncSession,
        payment_id: int,
    ) -> Payment:
        """Mark payment as refunded.

        Args:
            session: Database session.
            payment_id: Payment ID.

        Returns:
            Updated Payment record.

        Raises:
            ValueError: If payment not found or not in paid status.
        """
        payment = await session.get(Payment, payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.status != "paid":
            raise ValueError(
                f"Cannot refund payment in status {payment.status}. "
                "Only paid payments can be refunded."
            )

        payment.status = "refunded"
        await session.flush()

        logger.info(f"Payment {payment_id} marked as refunded")

        return payment

    async def get_user_payments(
        self,
        session: AsyncSession,
        user_id: int,
        *,
        status: str | None = None,
    ) -> list[Payment]:
        """Get all payments for a user.

        Args:
            session: Database session.
            user_id: User ID.
            status: Optional filter by payment status.

        Returns:
            List of Payment records.
        """
        stmt = select(Payment).where(Payment.user_id == user_id)

        if status:
            stmt = stmt.where(Payment.status == status)

        stmt = stmt.order_by(Payment.created_at.desc())

        result = await session.execute(stmt)
        return list(result.scalars().all())


    async def get_payment_by_result(
        self,
        session: AsyncSession,
        result_id: int,
    ) -> Payment | None:
        """Get payment for a quiz result.

        Args:
            session: Database session.
            result_id: Quiz result ID.

        Returns:
            Payment record or None if not found.
        """
        stmt = (
            select(Payment)
            .where(Payment.result_id == result_id)
            .order_by(Payment.created_at.desc())
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()



# Global instance
payment_service = PaymentService()
