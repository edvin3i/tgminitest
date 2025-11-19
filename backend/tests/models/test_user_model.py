"""Tests for User model."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test creating a user."""
    user = User(
        telegram_id=444444444,
        username="testuser123",
        first_name="Test",
        last_name="User",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 444444444
    assert user.username == "testuser123"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.is_admin is False
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_repr(db_session: AsyncSession, test_user: User) -> None:
    """Test user string representation."""
    repr_str = repr(test_user)

    assert "User" in repr_str
    assert str(test_user.id) in repr_str
    assert str(test_user.telegram_id) in repr_str


@pytest.mark.asyncio
async def test_user_to_dict(db_session: AsyncSession, test_user: User) -> None:
    """Test user to_dict method."""
    user_dict = test_user.to_dict()

    assert isinstance(user_dict, dict)
    assert user_dict["telegram_id"] == test_user.telegram_id
    assert user_dict["username"] == test_user.username
    assert user_dict["first_name"] == test_user.first_name


@pytest.mark.asyncio
async def test_user_unique_telegram_id(db_session: AsyncSession) -> None:
    """Test that telegram_id is unique."""
    user1 = User(telegram_id=555555555, first_name="User1")
    db_session.add(user1)
    await db_session.commit()

    user2 = User(telegram_id=555555555, first_name="User2")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
