"""Tests for user service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import (
    get_or_create_user,
    get_user_by_id,
    get_user_by_telegram_id,
    set_admin_status,
)


@pytest.mark.asyncio
async def test_create_new_user(db_session: AsyncSession) -> None:
    """Test creating a new user."""
    user = await get_or_create_user(
        telegram_id=111111111,
        username="newuser",
        first_name="New",
        last_name="User",
    )

    assert user.id is not None
    assert user.telegram_id == 111111111
    assert user.username == "newuser"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.is_admin is False


@pytest.mark.asyncio
async def test_get_existing_user(db_session: AsyncSession, test_user: User) -> None:
    """Test getting an existing user."""
    user = await get_or_create_user(
        telegram_id=test_user.telegram_id,
        username="updatedusername",
        first_name="Updated",
    )

    assert user.id == test_user.id
    assert user.telegram_id == test_user.telegram_id
    assert user.username == "updatedusername"  # Should be updated
    assert user.first_name == "Updated"  # Should be updated


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(db_session: AsyncSession, test_user: User) -> None:
    """Test getting user by Telegram ID."""
    user = await get_user_by_telegram_id(test_user.telegram_id)

    assert user is not None
    assert user.id == test_user.id
    assert user.telegram_id == test_user.telegram_id


@pytest.mark.asyncio
async def test_get_user_by_telegram_id_not_found(db_session: AsyncSession) -> None:
    """Test getting user by non-existent Telegram ID."""
    user = await get_user_by_telegram_id(999999999)

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession, test_user: User) -> None:
    """Test getting user by database ID."""
    user = await get_user_by_id(test_user.id)

    assert user is not None
    assert user.id == test_user.id
    assert user.telegram_id == test_user.telegram_id


@pytest.mark.asyncio
async def test_set_admin_status(db_session: AsyncSession, test_user: User) -> None:
    """Test setting admin status for a user."""
    # Make user admin
    user = await set_admin_status(test_user.telegram_id, True)

    assert user is not None
    assert user.is_admin is True

    # Remove admin status
    user = await set_admin_status(test_user.telegram_id, False)

    assert user is not None
    assert user.is_admin is False


@pytest.mark.asyncio
async def test_user_full_name_property(db_session: AsyncSession) -> None:
    """Test user full_name property."""
    # User with both first and last name
    user1 = await get_or_create_user(
        telegram_id=222222222,
        first_name="John",
        last_name="Doe",
    )
    assert user1.full_name == "John Doe"

    # User with only first name
    user2 = await get_or_create_user(
        telegram_id=333333333,
        first_name="Jane",
    )
    assert user2.full_name == "Jane"
