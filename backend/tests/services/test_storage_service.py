"""Tests for IPFS storage service using Pinata."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.services.ton.storage_service import StorageService


@pytest.fixture
def storage_service() -> StorageService:
    """Create storage service instance.

    Returns:
        StorageService instance.
    """
    return StorageService()


@pytest.fixture
def sample_image_data() -> bytes:
    """Create sample PNG image data.

    Returns:
        PNG image as bytes.
    """
    img = Image.new("RGB", (100, 100), color="red")
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def large_image_data() -> bytes:
    """Create large PNG image data (needs optimization).

    Returns:
        Large PNG image as bytes.
    """
    img = Image.new("RGB", (2048, 2048), color="blue")
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def rgba_image_data() -> bytes:
    """Create RGBA PNG image data.

    Returns:
        RGBA PNG image as bytes.
    """
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


# ==================== Image Upload Tests ====================


@pytest.mark.asyncio
async def test_upload_image_success(
    storage_service: StorageService,
    sample_image_data: bytes,
) -> None:
    """Test successful image upload to IPFS."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"IpfsHash": "QmTest123"})

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        ipfs_hash = await storage_service.upload_image(
            image_data=sample_image_data,
            filename="test.png",
            optimize=False,  # Skip optimization for speed
        )

    assert ipfs_hash == "QmTest123"
    mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_upload_image_with_optimization(
    storage_service: StorageService,
    large_image_data: bytes,
) -> None:
    """Test image upload with optimization enabled."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"IpfsHash": "QmOptimized456"})

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        ipfs_hash = await storage_service.upload_image(
            image_data=large_image_data,
            filename="large.png",
            optimize=True,
        )

    assert ipfs_hash == "QmOptimized456"
    # Optimization should be applied before upload
    call_args = mock_post.call_args
    form_data = call_args[1]["data"]
    # Verify that form data was created
    assert form_data is not None


@pytest.mark.asyncio
async def test_upload_image_failure(
    storage_service: StorageService,
    sample_image_data: bytes,
) -> None:
    """Test image upload failure."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match="Failed to upload image"):
            await storage_service.upload_image(
                image_data=sample_image_data,
                filename="test.png",
            )


# ==================== JSON Upload Tests ====================


@pytest.mark.asyncio
async def test_upload_json_success(storage_service: StorageService) -> None:
    """Test successful JSON metadata upload."""
    metadata = {
        "name": "Test NFT",
        "description": "Test description",
        "image": "ipfs://QmTest123",
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"IpfsHash": "QmMetadata789"})

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        ipfs_hash = await storage_service.upload_json(
            metadata=metadata,
            name="test_nft",
        )

    assert ipfs_hash == "QmMetadata789"
    mock_post.assert_called_once()

    # Verify JSON was properly formatted
    call_args = mock_post.call_args
    form_data = call_args[1]["data"]
    assert form_data is not None


@pytest.mark.asyncio
async def test_upload_json_failure(storage_service: StorageService) -> None:
    """Test JSON upload failure."""
    metadata = {"name": "Test"}

    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception, match="Failed to upload JSON"):
            await storage_service.upload_json(metadata=metadata, name="test")


# ==================== IPFS URL Tests ====================


@pytest.mark.asyncio
async def test_get_ipfs_url(storage_service: StorageService) -> None:
    """Test getting IPFS URL from hash."""
    ipfs_hash = "QmTest123"
    url = await storage_service.get_ipfs_url(ipfs_hash)

    assert url == "https://gateway.pinata.cloud/ipfs/QmTest123"
    assert url.startswith("https://")
    assert ipfs_hash in url


# ==================== Image Optimization Tests ====================


@pytest.mark.asyncio
async def test_optimize_image_resize(
    storage_service: StorageService,
    large_image_data: bytes,
) -> None:
    """Test that large images are resized."""
    optimized = await storage_service._optimize_image(large_image_data)

    # Should be smaller
    assert len(optimized) < len(large_image_data)

    # Verify it's still valid PNG
    img = Image.open(BytesIO(optimized))
    assert img.format == "PNG"
    # Should be resized to max 1024x1024
    assert img.size[0] <= 1024
    assert img.size[1] <= 1024


@pytest.mark.asyncio
async def test_optimize_image_rgba_to_rgb(
    storage_service: StorageService,
    rgba_image_data: bytes,
) -> None:
    """Test that RGBA images are converted to RGB."""
    optimized = await storage_service._optimize_image(rgba_image_data)

    # Verify it's valid PNG and RGB mode
    img = Image.open(BytesIO(optimized))
    assert img.format == "PNG"
    assert img.mode == "RGB"


@pytest.mark.asyncio
async def test_optimize_image_small_unchanged(
    storage_service: StorageService,
    sample_image_data: bytes,
) -> None:
    """Test that small images don't need resizing."""
    optimized = await storage_service._optimize_image(sample_image_data)

    # Should still be valid
    img = Image.open(BytesIO(optimized))
    assert img.format == "PNG"
    # Size should be 100x100 (no resize needed)
    assert img.size == (100, 100)


@pytest.mark.asyncio
async def test_optimize_image_error_fallback(
    storage_service: StorageService,
) -> None:
    """Test that optimization errors fall back to original."""
    invalid_data = b"not an image"

    # Should return original data on error
    result = await storage_service._optimize_image(invalid_data)
    assert result == invalid_data


# ==================== Unpin File Tests ====================


@pytest.mark.asyncio
async def test_unpin_file_success(storage_service: StorageService) -> None:
    """Test successful file unpinning."""
    mock_response = AsyncMock()
    mock_response.status = 200

    with patch("aiohttp.ClientSession.delete") as mock_delete:
        mock_delete.return_value.__aenter__.return_value = mock_response

        # Should not raise
        await storage_service.unpin_file("QmTest123")

    mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_unpin_file_not_found(storage_service: StorageService) -> None:
    """Test unpinning non-existent file (should not raise)."""
    mock_response = AsyncMock()
    mock_response.status = 404

    with patch("aiohttp.ClientSession.delete") as mock_delete:
        mock_delete.return_value.__aenter__.return_value = mock_response

        # Should not raise (best-effort cleanup)
        await storage_service.unpin_file("QmNonExistent")


@pytest.mark.asyncio
async def test_unpin_file_error(storage_service: StorageService) -> None:
    """Test that unpin errors are handled gracefully."""
    with patch("aiohttp.ClientSession.delete") as mock_delete:
        mock_delete.side_effect = Exception("Network error")

        # Should not raise (best-effort cleanup)
        await storage_service.unpin_file("QmTest123")


# ==================== Integration Tests ====================


@pytest.mark.asyncio
async def test_upload_flow_integration(
    storage_service: StorageService,
    sample_image_data: bytes,
) -> None:
    """Test complete upload flow: image + metadata."""
    # Mock image upload
    mock_image_response = AsyncMock()
    mock_image_response.status = 200
    mock_image_response.json = AsyncMock(return_value={"IpfsHash": "QmImage123"})

    # Mock metadata upload
    mock_metadata_response = AsyncMock()
    mock_metadata_response.status = 200
    mock_metadata_response.json = AsyncMock(return_value={"IpfsHash": "QmMetadata456"})

    with patch("aiohttp.ClientSession.post") as mock_post:
        # First call returns image hash, second returns metadata hash
        mock_post.return_value.__aenter__.side_effect = [
            mock_image_response,
            mock_metadata_response,
        ]

        # Upload image
        image_hash = await storage_service.upload_image(
            image_data=sample_image_data,
            filename="nft.png",
            optimize=False,
        )

        # Create metadata with image URL
        image_url = await storage_service.get_ipfs_url(image_hash)
        metadata = {
            "name": "Test NFT",
            "image": image_url,
        }

        # Upload metadata
        metadata_hash = await storage_service.upload_json(
            metadata=metadata,
            name="nft_metadata",
        )

    assert image_hash == "QmImage123"
    assert metadata_hash == "QmMetadata456"
    assert image_url == "https://gateway.pinata.cloud/ipfs/QmImage123"
    assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_service_configuration(storage_service: StorageService) -> None:
    """Test that service is properly configured."""
    # Verify configuration attributes exist
    assert hasattr(storage_service, "api_key")
    assert hasattr(storage_service, "secret_key")
    assert hasattr(storage_service, "base_url")
    assert hasattr(storage_service, "gateway_url")

    # Verify gateway URL format
    assert storage_service.gateway_url.startswith("https://")
    assert "pinata" in storage_service.gateway_url.lower()
