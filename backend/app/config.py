"""Application configuration using Pydantic Settings."""


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Telegram bot token from @BotFather")

    # Database
    POSTGRES_USER: str = Field(default="quizbot", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="changeme", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="telegram_quiz", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://quizbot:changeme@localhost:5432/telegram_quiz",
        description="Full database URL for SQLAlchemy",
    )

    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Database max overflow connections")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries (development only)")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    REDIS_PASSWORD: str = Field(default="", description="Redis password (if required)")

    # API Security
    SECRET_KEY: str = Field(
        default="changeme_insecure_secret_key",
        description="Secret key for JWT signing",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="JWT token expiration in minutes"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Application
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    TIMEZONE: str = Field(default="UTC", description="Application timezone")

    # TON Blockchain (Phase 3)
    TON_API_KEY: str = Field(default="", description="TON API key")
    TON_NETWORK: str = Field(default="testnet", description="TON network (testnet/mainnet)")
    NFT_COLLECTION_ADDRESS: str = Field(default="", description="NFT collection contract address")
    TON_WALLET_MNEMONIC: str = Field(default="", description="TON wallet mnemonic for minting")

    # IPFS Storage (Phase 3)
    IPFS_API_URL: str = Field(
        default="https://api.pinata.cloud", description="IPFS API endpoint"
    )
    IPFS_API_KEY: str = Field(default="", description="IPFS API key")
    IPFS_SECRET_KEY: str = Field(default="", description="IPFS secret key")
    TON_STORAGE_ENABLED: bool = Field(default=False, description="Use TON Storage instead of IPFS")

    # Payment Configuration (Phase 3)
    STARS_ENABLED: bool = Field(default=True, description="Enable Telegram Stars payments")
    TON_PAYMENT_ENABLED: bool = Field(default=False, description="Enable TON payments")
    NFT_MINT_PRICE_STARS: int = Field(default=10, description="NFT mint price in Telegram Stars")
    NFT_MINT_PRICE_TON: float = Field(default=0.1, description="NFT mint price in TON")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60, description="Max requests per minute per user"
    )
    QUIZ_LIMIT_PER_DAY: int = Field(
        default=10, description="Max quiz submissions per day per user"
    )
    MINT_LIMIT_PER_DAY: int = Field(default=5, description="Max NFT mints per day per user")

    # Admin
    ADMIN_TELEGRAM_IDS: list[int] = Field(
        default=[], description="Telegram user IDs with admin access"
    )

    @field_validator("ADMIN_TELEGRAM_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | list[int]) -> list[int]:
        """Parse admin IDs from comma-separated string or list."""
        if isinstance(v, str):
            if not v:
                return []
            return [int(admin_id.strip()) for admin_id in v.split(",") if admin_id.strip()]
        return v

    # Monitoring (Optional)
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")
    ANALYTICS_ID: str = Field(default="", description="Analytics tracking ID")

    # Webhooks (Phase 3)
    WEBHOOK_URL: str = Field(default="", description="Webhook URL for payment confirmations")
    WEBHOOK_SECRET: str = Field(default="", description="Webhook signature secret")

    # Development
    AUTO_RELOAD: bool = Field(default=True, description="Auto-reload on code changes")
    SHOW_ERROR_DETAILS: bool = Field(
        default=True, description="Show detailed error messages in responses"
    )


# Global settings instance
settings = Settings()
