"""State management service using Redis for quiz sessions."""

import json
from typing import Any

from loguru import logger
from redis import asyncio as aioredis

from app.config import settings


class StateService:
    """Redis-based state management for quiz sessions."""

    def __init__(self) -> None:
        """Initialize StateService with Redis connection."""
        self.redis: aioredis.Redis | None = None
        self.default_ttl = 1800  # 30 minutes

    async def connect(self) -> None:
        """Connect to Redis."""
        if self.redis is None:
            self.redis = await aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")

    def _get_quiz_key(self, user_id: int) -> str:
        """Generate Redis key for user's quiz session.

        Args:
            user_id: Telegram user ID.

        Returns:
            Redis key string.
        """
        return f"quiz:session:{user_id}"

    async def start_quiz(self, user_id: int, quiz_id: int) -> None:
        """Start a new quiz session for user.

        Args:
            user_id: Telegram user ID.
            quiz_id: Quiz database ID.
        """
        if not self.redis:
            await self.connect()

        session_data = {
            "quiz_id": quiz_id,
            "current_question": 0,
            "answers": [],
        }

        key = self._get_quiz_key(user_id)
        await self.redis.set(  # type: ignore
            key, json.dumps(session_data), ex=self.default_ttl
        )

        logger.info(f"Started quiz session for user {user_id}, quiz {quiz_id}")

    async def get_quiz_session(self, user_id: int) -> dict[str, Any] | None:
        """Get user's current quiz session.

        Args:
            user_id: Telegram user ID.

        Returns:
            Session data dict or None if no active session.
        """
        if not self.redis:
            await self.connect()

        key = self._get_quiz_key(user_id)
        data = await self.redis.get(key)  # type: ignore[union-attr]

        if data:
            result: dict[str, Any] = json.loads(data)
            return result
        return None

    async def save_answer(self, user_id: int, answer_id: int) -> None:
        """Save user's answer and advance to next question.

        Args:
            user_id: Telegram user ID.
            answer_id: Selected answer ID.
        """
        session = await self.get_quiz_session(user_id)
        if not session:
            raise ValueError(f"No active quiz session for user {user_id}")

        session["answers"].append(answer_id)
        session["current_question"] += 1

        key = self._get_quiz_key(user_id)
        await self.redis.set(  # type: ignore
            key, json.dumps(session), ex=self.default_ttl
        )

        logger.debug(
            f"Saved answer {answer_id} for user {user_id}, "
            f"now on question {session['current_question']}"
        )

    async def get_current_question_index(self, user_id: int) -> int:
        """Get current question index for user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Current question index (0-based).

        Raises:
            ValueError: If no active session exists.
        """
        session = await self.get_quiz_session(user_id)
        if not session:
            raise ValueError(f"No active quiz session for user {user_id}")

        current_question: int = session["current_question"]
        return current_question

    async def get_answers(self, user_id: int) -> list[int]:
        """Get all answers submitted by user in current session.

        Args:
            user_id: Telegram user ID.

        Returns:
            List of answer IDs.

        Raises:
            ValueError: If no active session exists.
        """
        session = await self.get_quiz_session(user_id)
        if not session:
            raise ValueError(f"No active quiz session for user {user_id}")

        answers: list[int] = session["answers"]
        return answers

    async def clear_quiz_session(self, user_id: int) -> None:
        """Clear user's quiz session.

        Args:
            user_id: Telegram user ID.
        """
        if not self.redis:
            await self.connect()

        key = self._get_quiz_key(user_id)
        await self.redis.delete(key)  # type: ignore

        logger.info(f"Cleared quiz session for user {user_id}")


# Global state service instance
state_service = StateService()
