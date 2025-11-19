"""NFT schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class NFTMintRequest(BaseModel):
    """Request to initiate NFT minting."""

    result_id: int = Field(..., description="Quiz result ID to mint NFT for")
    provider: str = Field(
        default="telegram_stars",
        description="Payment provider (telegram_stars or ton_connect)",
    )


class PaymentInvoiceResponse(BaseModel):
    """Payment invoice response."""

    payment_id: int = Field(..., description="Payment ID")
    result_id: int = Field(..., description="Quiz result ID")
    amount: int = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code (STARS or TON)")
    provider: str = Field(..., description="Payment provider")
    status: str = Field(..., description="Payment status")
    invoice_data: dict | None = Field(
        None, description="Invoice data for Telegram Stars"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class NFTMintStatusResponse(BaseModel):
    """NFT minting status response."""

    transaction_id: int = Field(..., description="Mint transaction ID")
    result_id: int = Field(..., description="Quiz result ID")
    status: str = Field(..., description="Minting status")
    nft_address: str | None = Field(None, description="NFT contract address")
    transaction_hash: str | None = Field(None, description="Blockchain transaction hash")
    ipfs_hash: str | None = Field(None, description="IPFS metadata hash")
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Transaction creation time")
    confirmed_at: datetime | None = Field(None, description="Confirmation time")

    class Config:
        """Pydantic config."""

        from_attributes = True


class NFTMetadataResponse(BaseModel):
    """NFT metadata response."""

    name: str = Field(..., description="NFT name")
    description: str = Field(..., description="NFT description")
    image: str = Field(..., description="NFT image URL")
    attributes: list[dict] = Field(..., description="NFT attributes")
    metadata_url: str = Field(..., description="Metadata URL")

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserNFTResponse(BaseModel):
    """User's NFT response."""

    nft_address: str = Field(..., description="NFT contract address")
    transaction_hash: str | None = Field(None, description="Transaction hash")
    minted_at: datetime = Field(..., description="Minting timestamp")
    result_id: int = Field(..., description="Quiz result ID")
    metadata: NFTMetadataResponse | None = Field(None, description="NFT metadata")

    class Config:
        """Pydantic config."""

        from_attributes = True


class MintConfirmRequest(BaseModel):
    """Request to confirm payment and trigger minting."""

    payment_id: int = Field(..., description="Payment ID to confirm")


class MintConfirmResponse(BaseModel):
    """Response after confirming payment and triggering mint."""

    success: bool = Field(..., description="Whether minting was initiated")
    transaction_id: int | None = Field(None, description="Mint transaction ID")
    message: str = Field(..., description="Status message")

    class Config:
        """Pydantic config."""

        from_attributes = True
