"""NFT minting service for TON blockchain integration."""

import asyncio
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz
from app.models.result import MintTransaction, NFTMetadata, QuizResult
from app.services.ton.metadata_service import metadata_service
from app.services.ton.storage_service import storage_service
from app.services.ton.wallet_service import wallet_service


class NFTService:
    """Service for minting NFTs on TON blockchain."""

    def __init__(self) -> None:
        """Initialize NFT service."""
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def mint_nft(
        self,
        session: AsyncSession,
        quiz_result: QuizResult,
        quiz: Quiz,
    ) -> MintTransaction:
        """Mint NFT for quiz result.

        Args:
            session: Database session.
            quiz_result: Quiz result to mint NFT for.
            quiz: Quiz object.

        Returns:
            MintTransaction record.

        Raises:
            Exception: If minting fails after retries.
        """
        mint_tx = None
        try:
            # Create initial mint transaction record
            mint_tx = MintTransaction(
                user_id=quiz_result.user_id,
                result_id=quiz_result.id,
                status="pending",
            )
            session.add(mint_tx)
            await session.flush()

            logger.info(f"Starting NFT minting for result {quiz_result.id}")

            # Step 1: Generate or get image
            image_data = await self._get_result_image(quiz_result)

            # Step 2: Upload image to IPFS
            mint_tx.status = "uploading_image"
            await session.flush()

            image_hash = await storage_service.upload_image(
                image_data,
                filename=f"result_{quiz_result.id}.png",
            )
            image_url = await storage_service.get_ipfs_url(image_hash)

            logger.info(f"Image uploaded to IPFS: {image_hash}")

            # Step 3: Generate metadata
            mint_tx.status = "generating_metadata"
            await session.flush()

            nft_metadata_dict = metadata_service.generate_nft_metadata(
                quiz_result=quiz_result,
                quiz=quiz,
                image_url=image_url,
            )

            # Validate metadata
            if not metadata_service.validate_metadata(nft_metadata_dict):
                raise ValueError("Generated metadata is invalid")

            # Step 4: Upload metadata to IPFS
            mint_tx.status = "uploading_metadata"
            await session.flush()

            metadata_hash = await storage_service.upload_json(
                nft_metadata_dict,
                name=f"result_{quiz_result.id}",
            )
            metadata_url = await storage_service.get_ipfs_url(metadata_hash)

            logger.info(f"Metadata uploaded to IPFS: {metadata_hash}")

            # Step 5: Store NFT metadata in database
            nft_metadata = NFTMetadata(
                result_id=quiz_result.id,
                name=nft_metadata_dict["name"],
                description=nft_metadata_dict["description"],
                image_url=image_url,
                metadata_url=metadata_url,
                attributes=nft_metadata_dict.get("attributes", []),
            )
            session.add(nft_metadata)
            await session.flush()

            # Step 6: Mint NFT on TON blockchain
            mint_tx.status = "minting"
            await session.flush()

            nft_address = await self._mint_on_blockchain(
                metadata_url=metadata_url,
                owner_address=quiz_result.user.telegram_id,  # Placeholder
            )

            # Step 7: Update transaction with success
            mint_tx.status = "completed"
            mint_tx.nft_address = nft_address
            mint_tx.transaction_hash = f"tx_{nft_address}"  # Placeholder
            mint_tx.ipfs_hash = metadata_hash

            # Update quiz result
            quiz_result.nft_minted = True
            quiz_result.nft_address = nft_address

            await session.commit()

            logger.info(
                f"NFT minted successfully: {nft_address} for result {quiz_result.id}"
            )
            return mint_tx

        except Exception as e:
            logger.exception(f"Error minting NFT for result {quiz_result.id}: {e}")

            if mint_tx:
                mint_tx.status = "failed"
                mint_tx.error_message = str(e)
                await session.commit()

            raise

    async def _get_result_image(self, quiz_result: QuizResult) -> bytes:
        """Get or generate image for quiz result.

        Args:
            quiz_result: Quiz result object.

        Returns:
            Image data as bytes.
        """
        # For now, generate a default image
        # In production, you might fetch from a pre-designed template
        return await metadata_service.generate_default_image_data(
            quiz_result.result_type
        )

    async def _mint_on_blockchain(
        self,
        metadata_url: str,
        owner_address: int | str,
    ) -> str:
        """Mint NFT on TON blockchain.

        Args:
            metadata_url: IPFS URL to NFT metadata.
            owner_address: Owner's address or Telegram ID.

        Returns:
            NFT contract address.

        Note:
            This is a placeholder implementation. In production, this will:
            1. Check wallet balance
            2. Create NFT mint message
            3. Send transaction to NFT collection contract
            4. Wait for confirmation
            5. Return NFT item contract address
        """
        # Placeholder implementation
        # TODO: Implement actual TON blockchain minting when collection is deployed

        # Check wallet health
        health = await wallet_service.health_check()
        if not health["healthy"]:
            raise RuntimeError(f"Wallet unhealthy: {health.get('error', 'Unknown')}")

        logger.info(
            f"[PLACEHOLDER] Minting NFT with metadata: {metadata_url} "
            f"for owner: {owner_address}"
        )

        # Simulate blockchain delay
        await asyncio.sleep(0.5)

        # Generate placeholder NFT address
        # In production, this would be the actual NFT item contract address
        nft_address = f"EQD...{owner_address}"

        logger.info(f"[PLACEHOLDER] NFT minted at address: {nft_address}")

        return nft_address

    async def retry_failed_mint(
        self,
        session: AsyncSession,
        mint_tx_id: int,
    ) -> MintTransaction:
        """Retry a failed mint transaction.

        Args:
            session: Database session.
            mint_tx_id: MintTransaction ID to retry.

        Returns:
            Updated MintTransaction.

        Raises:
            ValueError: If transaction not found or not in failed state.
        """
        mint_tx = await session.get(MintTransaction, mint_tx_id)

        if not mint_tx:
            raise ValueError(f"MintTransaction {mint_tx_id} not found")

        if mint_tx.status != "failed":
            raise ValueError(
                f"Cannot retry transaction in status: {mint_tx.status}. "
                "Only 'failed' transactions can be retried."
            )

        # Get the quiz result and quiz
        quiz_result = mint_tx.result
        quiz = quiz_result.quiz

        # Reset transaction
        mint_tx.status = "pending"
        mint_tx.error_message = None
        mint_tx.retry_count = (mint_tx.retry_count or 0) + 1

        if mint_tx.retry_count > self.max_retries:
            raise ValueError(
                f"Maximum retries ({self.max_retries}) exceeded for transaction {mint_tx_id}"
            )

        await session.flush()

        logger.info(
            f"Retrying mint transaction {mint_tx_id} "
            f"(attempt {mint_tx.retry_count}/{self.max_retries})"
        )

        # Retry minting (will create new transaction internally)
        return await self.mint_nft(session, quiz_result, quiz)

    async def get_nft_metadata(
        self,
        session: AsyncSession,
        nft_address: str,
    ) -> dict[str, Any] | None:
        """Get NFT metadata by address.

        Args:
            session: Database session.
            nft_address: NFT contract address.

        Returns:
            NFT metadata dictionary or None if not found.
        """
        # Query database for NFT metadata
        stmt = select(NFTMetadata).join(QuizResult).join(MintTransaction).where(
            MintTransaction.nft_address == nft_address
        )

        result = await session.execute(stmt)
        nft_metadata = result.scalar_one_or_none()

        if not nft_metadata:
            return None

        return {
            "name": nft_metadata.name,
            "description": nft_metadata.description,
            "image": nft_metadata.image_url,
            "attributes": nft_metadata.attributes,
            "metadata_url": nft_metadata.metadata_url,
        }

    async def get_user_nfts(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> list[dict[str, Any]]:
        """Get all NFTs minted by a user.

        Args:
            session: Database session.
            user_id: User ID.

        Returns:
            List of NFT data dictionaries.
        """
        stmt = (
            select(MintTransaction)
            .where(
                MintTransaction.user_id == user_id,
                MintTransaction.status == "completed",
            )
            .order_by(MintTransaction.created_at.desc())
        )

        result = await session.execute(stmt)
        mint_txs = result.scalars().all()

        nfts = []
        for tx in mint_txs:
            if not tx.nft_address:
                continue

            # Get metadata
            metadata = await self.get_nft_metadata(session, tx.nft_address)

            nfts.append(
                {
                    "nft_address": tx.nft_address,
                    "transaction_hash": tx.transaction_hash,
                    "minted_at": tx.created_at,
                    "result_id": tx.result_id,
                    "metadata": metadata,
                }
            )

        return nfts


# Global instance
nft_service = NFTService()
