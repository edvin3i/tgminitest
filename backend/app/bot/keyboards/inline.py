"""Inline keyboard builders for the bot."""

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main menu keyboard.

    Returns:
        InlineKeyboardMarkup with main menu buttons.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🎯 Browse Quizzes", callback_data="browse_quizzes")
    )
    builder.row(
        InlineKeyboardButton(text="🖼️ My NFTs", callback_data="my_nfts"),
        InlineKeyboardButton(text="📊 My Stats", callback_data="my_stats"),
    )
    builder.row(InlineKeyboardButton(text="ℹ️ Help", callback_data="help"))

    return builder.as_markup()


def get_quiz_selection_keyboard(quizzes: list[Any]) -> InlineKeyboardMarkup:
    """Build quiz selection keyboard.

    Args:
        quizzes: List of quiz objects with id and title.

    Returns:
        InlineKeyboardMarkup with quiz selection buttons.
    """
    builder = InlineKeyboardBuilder()

    # Add button for each quiz
    for quiz in quizzes:
        builder.row(
            InlineKeyboardButton(
                text=f"🎯 {quiz.title}", callback_data=f"quiz:{quiz.id}"
            )
        )

    # Add back button
    builder.row(InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu"))

    return builder.as_markup()


def get_quiz_answer_keyboard(answers: list[Any], question_index: int) -> InlineKeyboardMarkup:
    """Build answer selection keyboard for a quiz question.

    Args:
        answers: List of answer objects with id and text.
        question_index: Current question index.

    Returns:
        InlineKeyboardMarkup with answer buttons.
    """
    builder = InlineKeyboardBuilder()

    # Add button for each answer
    for answer in answers:
        builder.row(
            InlineKeyboardButton(
                text=answer.text,
                callback_data=f"answer:{question_index}:{answer.id}",
            )
        )

    return builder.as_markup()


def get_result_keyboard(result_id: int, nft_minted: bool = False) -> InlineKeyboardMarkup:
    """Build keyboard for quiz result screen.

    Args:
        result_id: Quiz result ID.
        nft_minted: Whether NFT has already been minted.

    Returns:
        InlineKeyboardMarkup with result action buttons.
    """
    builder = InlineKeyboardBuilder()

    if not nft_minted:
        builder.row(
            InlineKeyboardButton(text="🎨 Mint NFT", callback_data=f"mint_nft:{result_id}")
        )

    builder.row(
        InlineKeyboardButton(text="📤 Share Result", callback_data=f"share_result:{result_id}"),
        InlineKeyboardButton(text="🔁 Take Another Quiz", callback_data="browse_quizzes"),
    )

    return builder.as_markup()
