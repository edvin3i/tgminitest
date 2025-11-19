"""User service for managing user operations."""

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.user import User


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str = "User",
    last_name: str | None = None,
) -> User:
    """Get existing user or create new one.

    Args:
        telegram_id: Telegram user ID.
        username: Telegram username (optional).
        first_name: User's first name.
        last_name: User's last name (optional).

    Returns:
        User: User model instance.

    Example:
        ```python
        user = await get_or_create_user(
            telegram_id=123456789,
            username="john_doe",
            first_name="John",
            last_name="Doe"
        )
        ```
    """
    async with AsyncSessionLocal() as session:
        # Try to find existing user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update user information if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True

            if updated:
                await session.commit()
                await session.refresh(user)
        else:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Get user by Telegram ID.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        User or None if not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: int) -> User | None:
    """Get user by database ID.

    Args:
        user_id: Database user ID.

    Returns:
        User or None if not found.
    """
    async with AsyncSessionLocal() as session:
        return await session.get(User, user_id)


async def set_admin_status(telegram_id: int, is_admin: bool) -> User | None:
    """Set admin status for a user.

    Args:
        telegram_id: Telegram user ID.
        is_admin: Admin status to set.

    Returns:
        Updated user or None if not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.is_admin = is_admin
            await session.commit()
            await session.refresh(user)

        return user
