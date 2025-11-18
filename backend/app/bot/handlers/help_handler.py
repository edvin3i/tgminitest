"""Handler for /help command."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command.

    Displays help information about the bot.

    Args:
        message: Telegram message object.
    """
    try:
        help_text = (
            "📚 <b>Help & Commands</b>\n\n"
            "<b>Available Commands:</b>\n"
            "/start - Start the bot and see main menu\n"
            "/help - Show this help message\n"
            "/quiz - Browse available quizzes\n"
            "/mynfts - View your minted NFTs (coming soon)\n\n"
            "<b>How to use:</b>\n"
            "1. Use /quiz or click 'Browse Quizzes' button\n"
            "2. Select a quiz you like\n"
            "3. Answer all questions honestly\n"
            "4. See your result and mint it as NFT\n\n"
            "<b>About NFTs:</b>\n"
            "• Each quiz result can be minted as a unique NFT\n"
            "• NFTs are stored on TON blockchain\n"
            "• You can view and share your collection\n\n"
            "Need more help? Contact @support"
        )

        await message.answer(help_text)

    except Exception as e:
        logger.exception(f"Error in cmd_help: {e}")
        await message.answer("Sorry, an error occurred. Please try again.")
