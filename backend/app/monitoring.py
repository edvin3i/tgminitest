"""Monitoring and error tracking integration."""

import logging
import sys
from typing import Any

from loguru import logger

from app.config import settings


def setup_sentry() -> None:
    """Initialize Sentry for error tracking.

    Only initializes if SENTRY_DSN is configured.
    Integrates with FastAPI, SQLAlchemy, Redis, and asyncio.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        # Configure logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            # Performance monitoring
            traces_sample_rate=getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1),
            # Error sampling (1.0 = 100% of errors)
            sample_rate=1.0,
            # Integrations
            integrations=[
                sentry_logging,
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
            ],
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            max_breadcrumbs=50,
            debug=settings.DEBUG,
            # Release tracking (optional, set via environment)
            release=getattr(settings, "APP_VERSION", None),
        )

        logger.info(
            f"Sentry initialized successfully for environment: {settings.ENVIRONMENT}"
        )

    except ImportError:
        logger.warning(
            "Sentry SDK not installed. Install with: uv pip install sentry-sdk"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def setup_logging() -> None:
    """Configure loguru logging.

    Sets up:
    - Console logging with appropriate level
    - File logging with rotation (production)
    - JSON formatting (production) or pretty (development)
    - Structured logging with context
    """
    # Remove default handler
    logger.remove()

    # Determine log format
    if settings.ENVIRONMENT == "production":
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> | "
            "{extra}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )

    # File handler (production)
    if settings.ENVIRONMENT == "production":
        log_file = getattr(settings, "LOG_FILE_PATH", "/var/log/tgquiz/app.log")
        logger.add(
            log_file,
            rotation=getattr(settings, "LOG_ROTATION", "100 MB"),
            retention=getattr(settings, "LOG_RETENTION", "30 days"),
            compression="zip",
            format=log_format,
            level="INFO",
            serialize=getattr(settings, "LOG_FORMAT", "json") == "json",
            backtrace=True,
            diagnose=False,  # Don't include variables in production logs
        )

    logger.info(
        f"Logging configured: level={settings.LOG_LEVEL}, "
        f"environment={settings.ENVIRONMENT}"
    )


def capture_exception(
    error: Exception,
    context: dict[str, Any] | None = None,
    level: str = "error",
) -> None:
    """Capture an exception and send to monitoring systems.

    Args:
        error: The exception to capture
        context: Additional context to attach to the error
        level: Severity level (debug, info, warning, error, critical)

    Example:
        ```python
        try:
            result = await mint_nft(user_id, result_id)
        except Exception as e:
            capture_exception(e, context={
                "user_id": user_id,
                "result_id": result_id,
                "operation": "nft_minting"
            })
            raise
        ```
    """
    # Log with loguru
    log_func = getattr(logger, level, logger.error)
    log_message = f"Exception captured: {error}"

    if context:
        log_func(log_message, **context)
    else:
        log_func(log_message)

    # Send to Sentry if available
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, {"value": value})

                sentry_sdk.capture_exception(error)
        except ImportError:
            pass
        except Exception as sentry_error:
            logger.warning(f"Failed to send error to Sentry: {sentry_error}")


def capture_message(
    message: str,
    level: str = "info",
    context: dict[str, Any] | None = None,
) -> None:
    """Capture a message and send to monitoring systems.

    Args:
        message: The message to capture
        level: Severity level
        context: Additional context

    Example:
        ```python
        capture_message(
            "NFT minting completed successfully",
            level="info",
            context={
                "user_id": user_id,
                "nft_address": nft_address,
                "duration_ms": duration
            }
        )
        ```
    """
    # Log with loguru
    log_func = getattr(logger, level, logger.info)

    if context:
        log_func(message, **context)
    else:
        log_func(message)

    # Send to Sentry if available (only for warnings and above)
    if settings.SENTRY_DSN and level in ["warning", "error", "critical"]:
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, {"value": value})

                sentry_sdk.capture_message(message, level=level)
        except ImportError:
            pass
        except Exception as sentry_error:
            logger.warning(f"Failed to send message to Sentry: {sentry_error}")


def add_monitoring_context(**kwargs: Any) -> None:
    """Add context to all monitoring systems for the current scope.

    Args:
        **kwargs: Key-value pairs to add as context

    Example:
        ```python
        add_monitoring_context(
            user_id=user.id,
            telegram_id=user.telegram_id,
            request_id=request_id
        )
        ```
    """
    # Add to loguru context
    logger_context = logger.bind(**kwargs)

    # Add to Sentry if available
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk

            with sentry_sdk.configure_scope() as scope:
                for key, value in kwargs.items():
                    scope.set_tag(key, value)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to add Sentry context: {e}")


def initialize_monitoring() -> None:
    """Initialize all monitoring systems.

    Call this at application startup.
    """
    setup_logging()
    setup_sentry()

    logger.info(
        "Monitoring initialized",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        sentry_enabled=bool(settings.SENTRY_DSN),
    )
