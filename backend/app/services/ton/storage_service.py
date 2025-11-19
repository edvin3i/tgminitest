"""IPFS storage service for NFT metadata and images using Pinata."""

import json
from io import BytesIO
from typing import Any

import aiohttp
from loguru import logger
from PIL import Image

from app.config import settings


class StorageService:
    """Service for uploading NFT metadata and images to IPFS via Pinata."""

    def __init__(self) -> None:
        """Initialize StorageService with Pinata credentials."""
        self.api_key = settings.IPFS_API_KEY
        self.secret_key = settings.IPFS_SECRET_KEY
        self.base_url = settings.IPFS_API_URL
        self.gateway_url = "https://gateway.pinata.cloud/ipfs"

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        *,
        optimize: bool = True,
    ) -> str:
        """Upload image to IPFS via Pinata.

        Args:
            image_data: Image binary data.
            filename: Original filename.
            optimize: Whether to optimize image before upload.

        Returns:
            IPFS hash (CID) of the uploaded image.

        Raises:
            Exception: If upload fails.
        """
        try:
            # Optimize image if requested
            if optimize:
                image_data = await self._optimize_image(image_data)

            # Prepare form data
            form = aiohttp.FormData()
            form.add_field(
                "file",
                image_data,
                filename=filename,
                content_type="image/png",
            )

            # Prepare headers
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key,
            }

            # Upload to Pinata
            async with aiohttp.ClientSession() as session, session.post(
                f"{self.base_url}/pinning/pinFileToIPFS",
                data=form,
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Pinata upload failed: {error_text}")
                    raise Exception(f"Failed to upload image: {error_text}")

                result = await response.json()
                ipfs_hash: str = result["IpfsHash"]

                logger.info(f"Image uploaded to IPFS: {ipfs_hash}")
                return ipfs_hash

        except Exception as e:
            logger.exception(f"Error uploading image to IPFS: {e}")
            raise

    async def upload_json(
        self,
        metadata: dict[str, Any],
        name: str,
    ) -> str:
        """Upload JSON metadata to IPFS via Pinata.

        Args:
            metadata: NFT metadata dictionary.
            name: Metadata name for Pinata.

        Returns:
            IPFS hash (CID) of the uploaded JSON.

        Raises:
            Exception: If upload fails.
        """
        try:
            # Convert metadata to JSON
            json_data = json.dumps(metadata, indent=2)

            # Prepare form data
            form = aiohttp.FormData()
            form.add_field(
                "file",
                json_data.encode(),
                filename=f"{name}.json",
                content_type="application/json",
            )

            # Prepare headers
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key,
            }

            # Upload to Pinata
            async with aiohttp.ClientSession() as session, session.post(
                f"{self.base_url}/pinning/pinFileToIPFS",
                data=form,
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Pinata JSON upload failed: {error_text}")
                    raise Exception(f"Failed to upload JSON: {error_text}")

                result = await response.json()
                ipfs_hash: str = result["IpfsHash"]

                logger.info(f"Metadata uploaded to IPFS: {ipfs_hash}")
                return ipfs_hash

        except Exception as e:
            logger.exception(f"Error uploading JSON to IPFS: {e}")
            raise

    async def get_ipfs_url(self, ipfs_hash: str) -> str:
        """Get full IPFS URL from hash.

        Args:
            ipfs_hash: IPFS hash (CID).

        Returns:
            Full IPFS URL via Pinata gateway.
        """
        return f"{self.gateway_url}/{ipfs_hash}"

    async def _optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image for NFT (resize, compress).

        Args:
            image_data: Original image data.

        Returns:
            Optimized image data.
        """
        try:
            # Load image
            img = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")  # type: ignore[assignment]
                background.paste(img, mask=img.split()[-1] if len(img.split()) > 3 else None)
                img = background  # type: ignore[assignment]

            # Resize if too large (max 1024x1024)
            max_size = (1024, 1024)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save optimized image
            output = BytesIO()
            img.save(output, format="PNG", optimize=True, quality=85)
            optimized_data = output.getvalue()

            logger.debug(
                f"Image optimized: {len(image_data)} bytes -> {len(optimized_data)} bytes"
            )
            return optimized_data

        except Exception as e:
            logger.warning(f"Image optimization failed, using original: {e}")
            return image_data

    async def unpin_file(self, ipfs_hash: str) -> None:
        """Unpin file from IPFS (cleanup).

        Args:
            ipfs_hash: IPFS hash to unpin.
        """
        try:
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key,
            }

            async with aiohttp.ClientSession() as session, session.delete(
                f"{self.base_url}/pinning/unpin/{ipfs_hash}",
                headers=headers,
            ) as response:
                if response.status == 200:
                    logger.info(f"File unpinned from IPFS: {ipfs_hash}")
                else:
                    logger.warning(f"Failed to unpin file: {ipfs_hash}")

        except Exception as e:
            logger.error(f"Error unpinning file from IPFS: {e}")
            # Don't raise, cleanup is best-effort


# Global instance
storage_service = StorageService()
