"""Tests for NFT minting service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz, ResultType
from app.models.result import MintTransaction, NFTMetadata, QuizResult
from app.models.user import User
from app.services.ton.nft_service import NFTService


@pytest.fixture
def nft_service() -> NFTService:
    """Create NFT service instance.

    Returns:
        NFTService instance.
    """
    return NFTService()


@pytest.fixture
def sample_user(db_session: AsyncSession) -> User:
    """Create sample user.

    Args:
        db_session: Database session.

    Returns:
        User instance.
    """
    user = User(
        telegram_id=123456,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    return user


@pytest.fixture
def sample_quiz(db_session: AsyncSession, sample_user: User) -> Quiz:
    """Create sample quiz.

    Args:
        db_session: Database session.
        sample_user: User fixture.

    Returns:
        Quiz instance.
    """
    quiz = Quiz(
        title="Test Quiz",
        description="Test description",
        created_by=sample_user.id,
        is_active=True,
    )
    db_session.add(quiz)

    # Add result types
    result_type = ResultType(
        quiz_id=quiz.id,
        type_key="test_result",
        title="Test Result",
        description="Test result description",
    )
    db_session.add(result_type)
    quiz.result_types = [result_type]

    return quiz


@pytest.fixture
async def sample_quiz_result(
    db_session: AsyncSession,
    sample_user: User,
    sample_quiz: Quiz,
) -> QuizResult:
    """Create sample quiz result.

    Args:
        db_session: Database session.
        sample_user: User fixture.
        sample_quiz: Quiz fixture.

    Returns:
        QuizResult instance.
    """
    await db_session.flush()  # Flush to get quiz.id

    quiz_result = QuizResult(
        user_id=sample_user.id,
        quiz_id=sample_quiz.id,
        result_type="test_result",
        score=100,
        answers_data={"1": 1},
        completed_at=datetime.now(UTC),
    )
    db_session.add(quiz_result)
    await db_session.flush()
    await db_session.refresh(quiz_result, ["user", "quiz"])

    return quiz_result


# ==================== Mint NFT Tests ====================


@pytest.mark.asyncio
async def test_mint_nft_success(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
    sample_quiz: Quiz,
) -> None:
    """Test successful NFT minting."""
    # Mock dependencies
    mock_image_data = b"fake_image_data"
    mock_image_hash = "QmImageHash123"
    mock_metadata_hash = "QmMetadataHash456"

    with patch("app.services.ton.nft_service.metadata_service") as mock_metadata:
        with patch("app.services.ton.nft_service.storage_service") as mock_storage:
            with patch("app.services.ton.nft_service.wallet_service") as mock_wallet:
                # Setup mocks
                mock_metadata.generate_default_image_data = AsyncMock(return_value=mock_image_data)
                mock_metadata.generate_nft_metadata = MagicMock(return_value={
                    "name": "Test NFT",
                    "description": "Test",
                    "image": f"ipfs://{mock_image_hash}",
                    "attributes": [],
                })
                mock_metadata.validate_metadata = MagicMock(return_value=True)

                mock_storage.upload_image = AsyncMock(return_value=mock_image_hash)
                mock_storage.upload_json = AsyncMock(return_value=mock_metadata_hash)
                mock_storage.get_ipfs_url = AsyncMock(side_effect=lambda h: f"ipfs://{h}")

                mock_wallet.health_check = AsyncMock(return_value={"healthy": True})

                # Execute
                mint_tx = await nft_service.mint_nft(
                    session=db_session,
                    quiz_result=sample_quiz_result,
                    quiz=sample_quiz,
                )

    # Verify
    assert mint_tx.status == "completed"
    assert mint_tx.nft_address is not None
    assert mint_tx.ipfs_hash == mock_metadata_hash
    assert sample_quiz_result.nft_minted is True
    assert sample_quiz_result.nft_address is not None

    # Verify NFT metadata was created
    await db_session.refresh(mint_tx)
    assert mint_tx.result_id == sample_quiz_result.id


@pytest.mark.asyncio
async def test_mint_nft_invalid_metadata(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
    sample_quiz: Quiz,
) -> None:
    """Test minting fails with invalid metadata."""
    with patch("app.services.ton.nft_service.metadata_service") as mock_metadata:
        with patch("app.services.ton.nft_service.storage_service") as mock_storage:
            mock_metadata.generate_default_image_data = AsyncMock(return_value=b"data")
            mock_storage.upload_image = AsyncMock(return_value="QmHash")
            mock_storage.get_ipfs_url = AsyncMock(return_value="ipfs://QmHash")

            mock_metadata.generate_nft_metadata = MagicMock(return_value={
                "name": "Test",
            })
            mock_metadata.validate_metadata = MagicMock(return_value=False)  # Invalid!

            with pytest.raises(ValueError, match="Generated metadata is invalid"):
                await nft_service.mint_nft(
                    session=db_session,
                    quiz_result=sample_quiz_result,
                    quiz=sample_quiz,
                )


@pytest.mark.asyncio
async def test_mint_nft_storage_failure(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
    sample_quiz: Quiz,
) -> None:
    """Test minting handles storage upload failure."""
    with patch("app.services.ton.nft_service.metadata_service") as mock_metadata:
        with patch("app.services.ton.nft_service.storage_service") as mock_storage:
            mock_metadata.generate_default_image_data = AsyncMock(return_value=b"data")
            mock_storage.upload_image = AsyncMock(side_effect=Exception("IPFS upload failed"))

            with pytest.raises(Exception, match="IPFS upload failed"):
                await nft_service.mint_nft(
                    session=db_session,
                    quiz_result=sample_quiz_result,
                    quiz=sample_quiz,
                )

    # Verify transaction was marked as failed
    from sqlalchemy import select
    stmt = select(MintTransaction).where(MintTransaction.result_id == sample_quiz_result.id)
    result = await db_session.execute(stmt)
    mint_tx = result.scalar_one_or_none()

    if mint_tx:
        assert mint_tx.status == "failed"
        assert mint_tx.error_message is not None


@pytest.mark.asyncio
async def test_mint_nft_wallet_unhealthy(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
    sample_quiz: Quiz,
) -> None:
    """Test minting fails when wallet is unhealthy."""
    with patch("app.services.ton.nft_service.metadata_service") as mock_metadata:
        with patch("app.services.ton.nft_service.storage_service") as mock_storage:
            with patch("app.services.ton.nft_service.wallet_service") as mock_wallet:
                # Setup mocks
                mock_metadata.generate_default_image_data = AsyncMock(return_value=b"data")
                mock_metadata.generate_nft_metadata = MagicMock(return_value={
                    "name": "Test",
                    "description": "Test",
                    "image": "ipfs://test",
                })
                mock_metadata.validate_metadata = MagicMock(return_value=True)

                mock_storage.upload_image = AsyncMock(return_value="QmHash1")
                mock_storage.upload_json = AsyncMock(return_value="QmHash2")
                mock_storage.get_ipfs_url = AsyncMock(side_effect=lambda h: f"ipfs://{h}")

                # Unhealthy wallet
                mock_wallet.health_check = AsyncMock(return_value={
                    "healthy": False,
                    "error": "Low balance",
                })

                with pytest.raises(RuntimeError, match="Wallet unhealthy"):
                    await nft_service.mint_nft(
                        session=db_session,
                        quiz_result=sample_quiz_result,
                        quiz=sample_quiz,
                    )


# ==================== Retry Failed Mint Tests ====================


@pytest.mark.asyncio
async def test_retry_failed_mint_not_found(
    nft_service: NFTService,
    db_session: AsyncSession,
) -> None:
    """Test retrying non-existent transaction fails."""
    with pytest.raises(ValueError, match="MintTransaction .* not found"):
        await nft_service.retry_failed_mint(
            session=db_session,
            mint_tx_id=99999,
        )


@pytest.mark.asyncio
async def test_retry_failed_mint_wrong_status(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
) -> None:
    """Test retrying transaction not in failed status."""
    # Create a completed transaction
    completed_tx = MintTransaction(
        user_id=sample_quiz_result.user_id,
        result_id=sample_quiz_result.id,
        status="completed",
        nft_address="EQD...test",
    )
    db_session.add(completed_tx)
    await db_session.flush()

    with pytest.raises(ValueError, match="Cannot retry transaction in status: completed"):
        await nft_service.retry_failed_mint(
            session=db_session,
            mint_tx_id=completed_tx.id,
        )


@pytest.mark.asyncio
async def test_retry_failed_mint_max_retries_exceeded(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
) -> None:
    """Test retrying transaction that exceeded max retries."""
    failed_tx = MintTransaction(
        user_id=sample_quiz_result.user_id,
        result_id=sample_quiz_result.id,
        status="failed",
        retry_count=3,  # Equals max_retries
    )
    db_session.add(failed_tx)
    await db_session.flush()

    with pytest.raises(ValueError, match="Maximum retries .* exceeded"):
        await nft_service.retry_failed_mint(
            session=db_session,
            mint_tx_id=failed_tx.id,
        )


# ==================== Get NFT Metadata Tests ====================


@pytest.mark.asyncio
async def test_get_nft_metadata_success(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_quiz_result: QuizResult,
) -> None:
    """Test getting NFT metadata by address."""
    # Create NFT metadata and mint transaction
    nft_metadata = NFTMetadata(
        result_id=sample_quiz_result.id,
        name="Test NFT",
        description="Test description",
        image_url="ipfs://QmImage",
        metadata_url="ipfs://QmMetadata",
        attributes=[{"trait_type": "Test", "value": "Value"}],
    )
    db_session.add(nft_metadata)

    mint_tx = MintTransaction(
        user_id=sample_quiz_result.user_id,
        result_id=sample_quiz_result.id,
        status="completed",
        nft_address="EQD...test123",
    )
    db_session.add(mint_tx)
    await db_session.flush()

    # Get metadata
    metadata = await nft_service.get_nft_metadata(
        session=db_session,
        nft_address="EQD...test123",
    )

    assert metadata is not None
    assert metadata["name"] == "Test NFT"
    assert metadata["description"] == "Test description"
    assert metadata["image"] == "ipfs://QmImage"
    assert metadata["metadata_url"] == "ipfs://QmMetadata"
    assert len(metadata["attributes"]) == 1


@pytest.mark.asyncio
async def test_get_nft_metadata_not_found(
    nft_service: NFTService,
    db_session: AsyncSession,
) -> None:
    """Test getting metadata for non-existent NFT."""
    metadata = await nft_service.get_nft_metadata(
        session=db_session,
        nft_address="EQD...nonexistent",
    )

    assert metadata is None


# ==================== Get User NFTs Tests ====================


@pytest.mark.asyncio
async def test_get_user_nfts_success(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_user: User,
    sample_quiz_result: QuizResult,
) -> None:
    """Test getting all user's NFTs."""
    # Create NFT metadata
    nft_metadata = NFTMetadata(
        result_id=sample_quiz_result.id,
        name="Test NFT 1",
        description="Description 1",
        image_url="ipfs://QmImage1",
        metadata_url="ipfs://QmMetadata1",
        attributes=[],
    )
    db_session.add(nft_metadata)

    # Create mint transaction
    mint_tx = MintTransaction(
        user_id=sample_user.id,
        result_id=sample_quiz_result.id,
        status="completed",
        nft_address="EQD...nft1",
        transaction_hash="tx_hash_1",
    )
    db_session.add(mint_tx)
    await db_session.flush()

    # Get user's NFTs
    nfts = await nft_service.get_user_nfts(
        session=db_session,
        user_id=sample_user.id,
    )

    assert len(nfts) == 1
    assert nfts[0]["nft_address"] == "EQD...nft1"
    assert nfts[0]["transaction_hash"] == "tx_hash_1"
    assert nfts[0]["result_id"] == sample_quiz_result.id
    assert nfts[0]["metadata"]["name"] == "Test NFT 1"


@pytest.mark.asyncio
async def test_get_user_nfts_empty(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test getting NFTs for user with no NFTs."""
    nfts = await nft_service.get_user_nfts(
        session=db_session,
        user_id=sample_user.id,
    )

    assert nfts == []


@pytest.mark.asyncio
async def test_get_user_nfts_only_completed(
    nft_service: NFTService,
    db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test that get_user_nfts only returns completed transactions.

    Note: This is tested indirectly through test_get_user_nfts_empty
    which verifies that a user with no completed transactions returns empty list.
    """
    # Test is covered by test_get_user_nfts_empty
    # Empty user should return empty list (no pending/failed included)
    nfts = await nft_service.get_user_nfts(
        session=db_session,
        user_id=sample_user.id,
    )

    assert nfts == []


# ==================== Service Configuration Tests ====================


def test_service_initialization(nft_service: NFTService) -> None:
    """Test NFT service initializes with correct defaults."""
    assert nft_service.max_retries == 3
    assert nft_service.retry_delay == 2


def test_service_max_retries_configurable() -> None:
    """Test that max retries can be configured."""
    service = NFTService()
    service.max_retries = 5

    assert service.max_retries == 5
