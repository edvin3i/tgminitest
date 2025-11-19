"""NFT minting handlers for Telegram bot."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    Message,
    PreCheckoutQuery,
)
from loguru import logger

from app.db.database import AsyncSessionLocal
from app.models.result import QuizResult
from app.services.payment_service import payment_service
from app.services.ton.nft_service import nft_service
from app.services.user_service import get_user_by_telegram_id

router = Router(name="nft")


@router.callback_query(F.data.startswith("mint_nft:"))
async def initiate_nft_mint(callback: CallbackQuery) -> None:
    """Handle NFT mint button click.

    Args:
        callback: Callback query with result_id.
    """
    try:
        if not callback.from_user or not callback.message:
            return

        # Extract result_id
        result_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]

        # Get user
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("User not found. Please /start the bot first.", show_alert=True)
            return

        # Create payment using database session
        async with AsyncSessionLocal() as db:
            try:
                payment = await payment_service.create_mint_payment(
                    session=db,
                    user_id=user.id,
                    result_id=result_id,
                    provider="telegram_stars",
                )
                await db.commit()

                # Get quiz result for invoice details
                quiz_result = await db.get(QuizResult, result_id)
                if not quiz_result:
                    await callback.answer("Quiz result not found!", show_alert=True)
                    return

                await db.refresh(quiz_result, ["quiz"])

                # Create Stars invoice
                invoice_data = payment_service.create_stars_invoice(
                    payment=payment,
                    title="Mint Quiz Result NFT",
                    description=f"Mint your '{quiz_result.result_type}' result as a unique NFT on TON blockchain",
                )

                # Send invoice to user
                if callback.message.chat:
                    await callback.message.bot.send_invoice(  # type: ignore[union-attr]
                        chat_id=callback.message.chat.id,
                        **invoice_data,
                    )

                    await callback.answer("💰 Payment invoice sent! Complete payment to mint your NFT.")
                else:
                    await callback.answer("Error sending invoice. Please try again.", show_alert=True)

            except ValueError as e:
                await callback.answer(str(e), show_alert=True)
                return

    except Exception as e:
        logger.exception(f"Error initiating NFT mint: {e}")
        await callback.answer(
            "Error initiating NFT minting. Please try again later.",
            show_alert=True,
        )


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    """Handle pre-checkout query for payment validation.

    Args:
        pre_checkout_query: Pre-checkout query from Telegram.
    """
    try:
        invoice_payload = pre_checkout_query.invoice_payload

        # Validate payment
        async with AsyncSessionLocal() as db:
            is_valid, error_message = await payment_service.handle_pre_checkout(
                session=db,
                invoice_payload=invoice_payload,
            )

            if is_valid:
                await pre_checkout_query.answer(ok=True)
            else:
                await pre_checkout_query.answer(
                    ok=False,
                    error_message=error_message or "Payment validation failed",
                )

    except Exception as e:
        logger.exception(f"Error in pre-checkout handler: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Validation error")


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    """Handle successful payment and trigger NFT minting.

    Args:
        message: Message with successful_payment data.
    """
    try:
        if not message.successful_payment or not message.from_user:
            return

        payment_data = message.successful_payment
        invoice_payload = payment_data.invoice_payload
        telegram_payment_charge_id = payment_data.telegram_payment_charge_id
        provider_payment_charge_id = payment_data.provider_payment_charge_id

        # Update payment status
        async with AsyncSessionLocal() as db:
            try:
                payment = await payment_service.handle_successful_payment(
                    session=db,
                    invoice_payload=invoice_payload,
                    telegram_payment_charge_id=telegram_payment_charge_id,
                    provider_payment_charge_id=provider_payment_charge_id,
                )

                # Get quiz result and quiz
                quiz_result = await db.get(QuizResult, payment.result_id)
                if not quiz_result:
                    await message.answer("❌ Error: Quiz result not found")
                    return

                await db.refresh(quiz_result, ["quiz"])
                quiz = quiz_result.quiz

                await db.commit()

                # Send confirmation
                await message.answer(
                    "✅ <b>Payment Successful!</b>\n\n"
                    "🎨 Your NFT is now being minted on the TON blockchain.\n\n"
                    "This may take a few moments. You'll be notified when it's ready!"
                )

                # Trigger NFT minting (background process)
                try:
                    mint_tx = await nft_service.mint_nft(db, quiz_result, quiz)
                    await db.commit()

                    # Notify success
                    await message.answer(
                        "🎉 <b>NFT Minted Successfully!</b>\n\n"
                        f"🔗 NFT Address: <code>{mint_tx.nft_address}</code>\n"
                        f"📦 Transaction: <code>{mint_tx.transaction_hash}</code>\n\n"
                        f"🌐 IPFS: <code>{mint_tx.ipfs_hash}</code>\n\n"
                        "View your NFT collection with /mynfts"
                    )

                except Exception as mint_error:
                    logger.exception(f"Error minting NFT: {mint_error}")
                    await message.answer(
                        "⚠️ Payment received, but minting encountered an error.\n\n"
                        "Our team has been notified. Please contact support if the issue persists."
                    )

            except Exception as e:
                logger.exception(f"Error processing payment: {e}")
                await message.answer(
                    "❌ Error processing payment. Please contact support with "
                    f"payment ID: {telegram_payment_charge_id}"
                )

    except Exception as e:
        logger.exception(f"Error in successful payment handler: {e}")


@router.message(Command("mynfts"))
@router.callback_query(F.data == "my_nfts")
async def show_my_nfts(event: Message | CallbackQuery) -> None:
    """Show user's NFT collection.

    Args:
        event: Message or CallbackQuery to show NFTs.
    """
    try:
        # Extract user and message from event
        if isinstance(event, Message):
            from_user = event.from_user
            message = event
        else:  # CallbackQuery
            from_user = event.from_user
            message = event.message  # type: ignore[assignment]

        if not from_user or not message:
            return

        # Get user
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            if isinstance(event, CallbackQuery):
                await event.answer("User not found!", show_alert=True)
            else:
                await message.answer("User not found! Please /start the bot first.")
            return

        # Get user's NFTs
        async with AsyncSessionLocal() as db:
            nfts = await nft_service.get_user_nfts(db, user.id)

            if not nfts:
                text = (
                    "🖼️ <b>My NFT Collection</b>\n\n"
                    "You don't have any NFTs yet!\n\n"
                    "Complete quizzes and mint your results as unique NFTs.\n\n"
                    "Try /quiz to get started!"
                )
            else:
                text = f"🖼️ <b>My NFT Collection</b>\n\nYou have {len(nfts)} NFT(s):\n\n"

                for i, nft in enumerate(nfts, 1):
                    metadata = nft.get("metadata")
                    if metadata:
                        text += (
                            f"{i}. <b>{metadata['name']}</b>\n"
                            f"   🔗 <code>{nft['nft_address']}</code>\n"
                            f"   📅 {nft['minted_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                        )
                    else:
                        text += (
                            f"{i}. NFT #{nft['result_id']}\n"
                            f"   🔗 <code>{nft['nft_address']}</code>\n\n"
                        )

                text += "\n🌐 View on TON Explorer or your TON wallet"

            # Send response
            if isinstance(event, Message):
                await message.answer(text)
            else:  # CallbackQuery
                await message.edit_text(text)
                await event.answer()

    except Exception as e:
        logger.exception(f"Error showing NFTs: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer("Error loading NFTs. Please try again.", show_alert=True)
        else:
            await message.answer("Error loading NFTs. Please try again.")
