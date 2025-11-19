"""API dependencies for authentication and authorization."""

import hashlib
import hmac
import json
from typing import Annotated
from urllib.parse import unquote

from fastapi import Depends, Header, HTTPException, status
from loguru import logger

from app.config import settings
from app.models.user import User
from app.services.user_service import get_user_by_telegram_id


def validate_telegram_init_data(init_data: str) -> dict[str, str]:
    """Validate Telegram WebApp initData signature.

    Args:
        init_data: Telegram WebApp initData string.

    Returns:
        Validated data dictionary.

    Raises:
        HTTPException: If signature is invalid.

    Example:
        Data format: "query_id=...&user=...&auth_date=...&hash=..."
    """
    try:
        # Parse initData
        params = {}
        for item in init_data.split("&"):
            key, value = item.split("=", 1)
            params[key] = value

        # Extract hash
        received_hash = params.pop("hash", None)
        if not received_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing hash in initData",
            )

        # Create data check string
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )

        # Calculate expected hash
        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Verify hash
        if calculated_hash != received_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

        return params

    except ValueError as e:
        logger.error(f"Error parsing initData: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid initData format",
        ) from e


async def get_current_user(
    x_telegram_init_data: Annotated[str | None, Header()] = None,
) -> User:
    """Get current user from Telegram initData header.

    Args:
        x_telegram_init_data: Telegram WebApp initData from header.

    Returns:
        Current user.

    Raises:
        HTTPException: If authentication fails.
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header",
            headers={"WWW-Authenticate": "Telegram"},
        )

    # Validate initData
    params = validate_telegram_init_data(x_telegram_init_data)

    # Extract user data (usually in 'user' parameter as JSON)
    user_data_str = params.get("user")
    if not user_data_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user data in initData",
        )

    try:
        user_data = json.loads(unquote(user_data_str))
        telegram_id = user_data.get("id")

        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user data",
            )

        # Get or create user
        user = await get_user_by_telegram_id(telegram_id)
        if not user:
            # User doesn't exist, which means they haven't used the bot
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please start the bot first.",
            )

        return user

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data format",
        ) from e


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verify that current user is an admin.

    Args:
        current_user: Current authenticated user.

    Returns:
        Current admin user.

    Raises:
        HTTPException: If user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
