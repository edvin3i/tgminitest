"""Handler for /start command."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from app.bot.keyboards.inline import get_main_menu_keyboard
from app.services.user_service import get_or_create_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command.

    Creates or updates user in database and shows welcome message.

    Args:
        message: Telegram message object.
    """
    try:
        if not message.from_user:
            logger.warning("Received message without user information")
            await message.answer("Error: Unable to identify user.")
            return

        # Get or create user in database
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name or "User",
            last_name=message.from_user.last_name,
        )

        logger.info(f"User {user.telegram_id} started the bot")

        # Send welcome message with main menu
        welcome_text = (
            f"👋 <b>Welcome, {user.first_name}!</b>\n\n"
            "🎯 Take fun personality quizzes and mint unique NFTs on TON blockchain!\n\n"
            "✨ <b>How it works:</b>\n"
            "1. Choose a quiz from the menu\n"
            "2. Answer all questions\n"
            "3. Get your personalized result\n"
            "4. Mint it as an NFT! 🎨\n\n"
            "Ready to discover yourself? Let's start! 🚀"
        )

        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
        )

    except Exception as e:
        logger.exception(f"Error in cmd_start: {e}")
        await message.answer(
            "Sorry, something went wrong. Please try again later or contact support."
        )
