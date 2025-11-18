"""Quiz handlers for taking quizzes."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.bot.keyboards.inline import get_quiz_selection_keyboard

router = Router(name="quiz")


@router.message(Command("quiz"))
@router.callback_query(F.data == "browse_quizzes")
async def show_quiz_list(event: Message | CallbackQuery) -> None:
    """Show list of available quizzes.

    Args:
        event: Message or CallbackQuery object.
    """
    try:
        # TODO: Get actual quizzes from database
        # For now, show placeholder

        text = (
            "🎯 <b>Available Quizzes</b>\n\n"
            "Choose a quiz to take:\n"
            "(Quizzes will be available soon!)\n\n"
            "Coming attractions:\n"
            "• 🏰 Which Hogwarts House Are You?\n"
            "• 🌟 Discover Your Personality Type\n"
            "• 🎨 What's Your Creative Style?\n"
            "• 🦸 Which Superhero Are You?\n\n"
            "Stay tuned! Admin will add quizzes soon."
        )

        if isinstance(event, Message):
            await event.answer(text, reply_markup=get_quiz_selection_keyboard([]))
        else:
            await event.message.edit_text(
                text, reply_markup=get_quiz_selection_keyboard([])
            )

    except Exception as e:
        logger.exception(f"Error in show_quiz_list: {e}")
        error_text = "Sorry, couldn't load quizzes. Please try again."
        if isinstance(event, Message):
            await event.answer(error_text)
        else:
            await event.answer(error_text, show_alert=True)


@router.callback_query(F.data.startswith("quiz:"))
async def start_quiz(callback: CallbackQuery) -> None:
    """Start a quiz.

    Args:
        callback: Callback query from quiz selection.
    """
    try:
        # Extract quiz_id from callback data
        quiz_id = int(callback.data.split(":")[1])

        # TODO: Implement quiz flow
        # 1. Load quiz from database
        # 2. Initialize quiz state in Redis
        # 3. Show first question

        await callback.message.edit_text(
            f"🎯 <b>Quiz #{quiz_id}</b>\n\n"
            "Quiz functionality is coming soon!\n"
            "We're working on bringing you amazing quizzes. Stay tuned! 🚀"
        )

        await callback.answer()

    except Exception as e:
        logger.exception(f"Error in start_quiz: {e}")
        await callback.answer("Error loading quiz. Please try again.", show_alert=True)
