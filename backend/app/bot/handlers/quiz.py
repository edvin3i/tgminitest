"""Quiz handlers for taking quizzes."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.bot.keyboards.inline import (
    get_quiz_answer_keyboard,
    get_quiz_selection_keyboard,
    get_result_keyboard,
)
from app.services.quiz_service import (
    calculate_result,
    get_active_quizzes,
    get_quiz_by_id,
    get_result_type_info,
    save_quiz_result,
)
from app.services.state_service import state_service
from app.services.user_service import get_user_by_telegram_id

router = Router(name="quiz")


@router.message(Command("quiz"))
@router.callback_query(F.data == "browse_quizzes")
async def show_quiz_list(event: Message | CallbackQuery) -> None:
    """Show list of available quizzes.

    Args:
        event: Message or CallbackQuery object.
    """
    try:
        # Get active quizzes from database
        quizzes = await get_active_quizzes()

        if not quizzes:
            text = (
                "🎯 <b>Available Quizzes</b>\n\n"
                "No quizzes available yet!\n\n"
                "📝 Coming soon:\n"
                "• 🏰 Which Hogwarts House Are You?\n"
                "• 🌟 Discover Your Personality Type\n"
                "• 🎨 What's Your Creative Style?\n\n"
                "Check back later or ask an admin to create quizzes!"
            )
        else:
            text = (
                "🎯 <b>Available Quizzes</b>\n\n"
                f"Choose a quiz to take ({len(quizzes)} available):\n"
            )

        if isinstance(event, Message):
            await event.answer(text, reply_markup=get_quiz_selection_keyboard(quizzes))
        elif event.message:
            await event.message.edit_text(  # type: ignore[union-attr]
                text, reply_markup=get_quiz_selection_keyboard(quizzes)
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
        if not callback.from_user or not callback.message:
            return

        # Extract quiz_id from callback data
        quiz_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]

        # Load quiz from database with all questions and answers
        quiz = await get_quiz_by_id(quiz_id)
        if not quiz:
            await callback.answer("Quiz not found!", show_alert=True)
            return

        if not quiz.questions:
            await callback.answer("This quiz has no questions yet!", show_alert=True)
            return

        # Initialize quiz state in Redis
        await state_service.start_quiz(callback.from_user.id, quiz_id)

        # Show first question
        question = quiz.questions[0]
        text = (
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"📝 Question 1 of {len(quiz.questions)}\n\n"
            f"<b>{question.text}</b>"
        )

        await callback.message.edit_text(  # type: ignore[union-attr]
            text, reply_markup=get_quiz_answer_keyboard(question.answers, 0)
        )

        await callback.answer()

    except Exception as e:
        logger.exception(f"Error in start_quiz: {e}")
        await callback.answer("Error loading quiz. Please try again.", show_alert=True)


@router.callback_query(F.data.startswith("answer:"))
async def handle_answer(callback: CallbackQuery) -> None:
    """Handle user's answer selection.

    Args:
        callback: Callback query with answer selection.
    """
    try:
        if not callback.from_user or not callback.message:
            return

        # Parse callback data: answer:<question_index>:<answer_id>
        parts = callback.data.split(":")  # type: ignore[union-attr]
        answer_id = int(parts[2])

        # Get current quiz session
        session = await state_service.get_quiz_session(callback.from_user.id)
        if not session:
            await callback.answer("Quiz session expired. Please start again.", show_alert=True)
            return

        quiz_id = session["quiz_id"]
        quiz = await get_quiz_by_id(quiz_id)
        if not quiz:
            await callback.answer("Quiz not found!", show_alert=True)
            return

        # Save answer and advance
        await state_service.save_answer(callback.from_user.id, answer_id)

        # Check if there are more questions
        current_question_index = await state_service.get_current_question_index(
            callback.from_user.id
        )

        if current_question_index < len(quiz.questions):
            # Show next question
            question = quiz.questions[current_question_index]
            text = (
                f"🎯 <b>{quiz.title}</b>\n\n"
                f"📝 Question {current_question_index + 1} of {len(quiz.questions)}\n\n"
                f"<b>{question.text}</b>"
            )

            await callback.message.edit_text(  # type: ignore[union-attr]
                text,
                reply_markup=get_quiz_answer_keyboard(
                    question.answers, current_question_index
                ),
            )
        else:
            # Quiz completed - calculate result
            await show_result(callback)

        await callback.answer()

    except Exception as e:
        logger.exception(f"Error in handle_answer: {e}")
        await callback.answer("Error processing answer. Please try again.", show_alert=True)


async def show_result(callback: CallbackQuery) -> None:
    """Calculate and show quiz result.

    Args:
        callback: Callback query from last answer.
    """
    try:
        if not callback.from_user or not callback.message:
            return

        # Get answers from session
        answer_ids = await state_service.get_answers(callback.from_user.id)
        session = await state_service.get_quiz_session(callback.from_user.id)

        if not session:
            return

        quiz_id = session["quiz_id"]

        # Load quiz
        quiz = await get_quiz_by_id(quiz_id)
        if not quiz:
            return

        # Calculate result
        result_type, score = await calculate_result(quiz, answer_ids)

        # Get user
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            return

        # Save result to database
        quiz_result = await save_quiz_result(
            user_id=user.id,
            quiz_id=quiz_id,
            answer_ids=answer_ids,
            result_type=result_type,
            score=score,
        )

        # Get result type info
        result_info = await get_result_type_info(quiz_id, result_type)

        # Clear quiz session
        await state_service.clear_quiz_session(callback.from_user.id)

        # Display result
        if result_info:
            text = (
                f"🎉 <b>Quiz Completed!</b>\n\n"
                f"🎯 <b>{quiz.title}</b>\n\n"
                f"✨ <b>Your Result: {result_info.title}</b>\n\n"
                f"{result_info.description}\n\n"
                f"📊 Score: {score} points"
            )
        else:
            text = (
                f"🎉 <b>Quiz Completed!</b>\n\n"
                f"🎯 <b>{quiz.title}</b>\n\n"
                f"✨ <b>Your Result: {result_type}</b>\n\n"
                f"📊 Score: {score} points"
            )

        await callback.message.edit_text(  # type: ignore[union-attr]
            text, reply_markup=get_result_keyboard(quiz_result.id, nft_minted=False)
        )

    except Exception as e:
        logger.exception(f"Error in show_result: {e}")
        if callback.message:
            await callback.message.edit_text(  # type: ignore[union-attr]
                "❌ Error calculating result. Please try again later."
            )
