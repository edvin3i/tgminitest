"""NFT API endpoints for minting and management."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from loguru import logger
from sqlalchemy import select

from app.api.dependencies import CurrentUser
from app.db.database import DBSession
from app.models.quiz import Quiz
from app.models.result import MintTransaction, Payment, QuizResult
from app.schemas.nft import (
    MintConfirmRequest,
    MintConfirmResponse,
    NFTMetadataResponse,
    NFTMintRequest,
    NFTMintStatusResponse,
    PaymentInvoiceResponse,
    UserNFTResponse,
)
from app.services.payment_service import payment_service
from app.services.ton.nft_service import nft_service

router = APIRouter()


async def mint_nft_background(
    session: DBSession,
    quiz_result: QuizResult,
    quiz: Quiz,
) -> None:
    """Background task to mint NFT.

    Args:
        session: Database session.
        quiz_result: Quiz result to mint NFT for.
        quiz: Quiz object.
    """
    try:
        await nft_service.mint_nft(session, quiz_result, quiz)
        logger.info(f"Background minting completed for result {quiz_result.id}")
    except Exception as e:
        logger.exception(f"Background minting failed for result {quiz_result.id}: {e}")


@router.post("/mint", response_model=PaymentInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def initiate_nft_mint(
    request: NFTMintRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> PaymentInvoiceResponse:
    """Initiate NFT minting by creating a payment.

    Creates a payment record and returns invoice data for Telegram Stars payment.
    After payment is confirmed, the NFT will be minted.

    Args:
        request: Mint request with result_id and provider.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Payment invoice response.

    Raises:
        HTTPException: If result not found or validation fails.
    """
    try:
        # Create payment
        payment = await payment_service.create_mint_payment(
            session=db,
            user_id=current_user.id,
            result_id=request.result_id,
            provider=request.provider,
        )

        await db.commit()

        # For Telegram Stars, generate invoice data
        invoice_data = None
        if payment.provider == "telegram_stars":
            # Get quiz result for title
            result = await db.get(QuizResult, request.result_id)
            if result:
                await db.refresh(result, ["quiz"])
                invoice_data = payment_service.create_stars_invoice(
                    payment=payment,
                    title="Mint Quiz Result NFT",
                    description=f"Mint your '{result.result_type}' result as an NFT",
                )

        return PaymentInvoiceResponse(
            payment_id=payment.id,
            result_id=payment.result_id,
            amount=payment.amount,
            currency=payment.currency,
            provider=payment.provider,
            status=payment.status,
            invoice_data=invoice_data,
        )

    except ValueError as e:
        logger.error(f"Validation error in mint initiation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception(f"Error initiating NFT mint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate NFT minting",
        ) from e


@router.post("/mint/confirm", response_model=MintConfirmResponse)
async def confirm_mint_payment(
    request: MintConfirmRequest,
    db: DBSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> MintConfirmResponse:
    """Confirm payment and trigger NFT minting.

    This endpoint is called after payment is successful to trigger the actual minting.

    Args:
        request: Confirmation request with payment_id.
        db: Database session.
        current_user: Current authenticated user.
        background_tasks: Background task manager.

    Returns:
        Confirmation response.

    Raises:
        HTTPException: If payment not found or validation fails.
    """
    try:
        # Get payment
        payment = await db.get(Payment, request.payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {request.payment_id} not found",
            )

        # Verify ownership
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment does not belong to current user",
            )

        # Verify payment is paid
        if payment.status != "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment status is {payment.status}, expected 'paid'",
            )

        # Get quiz result and quiz
        quiz_result = await db.get(QuizResult, payment.result_id)
        if not quiz_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz result {payment.result_id} not found",
            )

        await db.refresh(quiz_result, ["quiz"])
        quiz = quiz_result.quiz

        # Check if already minting or minted
        if quiz_result.nft_minted:
            return MintConfirmResponse(
                success=False,
                transaction_id=None,
                message="NFT already minted for this result",
            )

        # Check for existing mint transaction
        stmt = select(MintTransaction).where(
            MintTransaction.result_id == quiz_result.id
        )
        result = await db.execute(stmt)
        existing_tx = result.scalar_one_or_none()

        if existing_tx and existing_tx.status in ["pending", "minting"]:
            return MintConfirmResponse(
                success=False,
                transaction_id=existing_tx.id,
                message=f"Minting already in progress (status: {existing_tx.status})",
            )

        # Trigger minting in background
        background_tasks.add_task(mint_nft_background, db, quiz_result, quiz)

        return MintConfirmResponse(
            success=True,
            transaction_id=None,  # Will be created in background
            message="NFT minting initiated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error confirming mint payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment",
        ) from e


@router.get("/status/{transaction_id}", response_model=NFTMintStatusResponse)
async def get_mint_status(
    transaction_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> NFTMintStatusResponse:
    """Get NFT minting status by transaction ID.

    Args:
        transaction_id: Mint transaction ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Minting status response.

    Raises:
        HTTPException: If transaction not found or unauthorized.
    """
    # Get mint transaction
    mint_tx = await db.get(MintTransaction, transaction_id)
    if not mint_tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mint transaction {transaction_id} not found",
        )

    # Verify ownership
    if mint_tx.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transaction does not belong to current user",
        )

    return NFTMintStatusResponse(
        transaction_id=mint_tx.id,
        result_id=mint_tx.result_id,
        status=mint_tx.status,
        nft_address=mint_tx.nft_address,
        transaction_hash=mint_tx.transaction_hash,
        ipfs_hash=mint_tx.ipfs_hash,
        error_message=mint_tx.error_message,
        created_at=mint_tx.created_at,
        confirmed_at=mint_tx.confirmed_at,
    )


@router.get("/metadata/{nft_address}", response_model=NFTMetadataResponse)
async def get_nft_metadata(
    nft_address: str,
    db: DBSession,
) -> NFTMetadataResponse:
    """Get NFT metadata by address.

    Args:
        nft_address: NFT contract address.
        db: Database session.

    Returns:
        NFT metadata response.

    Raises:
        HTTPException: If NFT not found.
    """
    metadata = await nft_service.get_nft_metadata(db, nft_address)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NFT {nft_address} not found",
        )

    return NFTMetadataResponse(
        name=metadata["name"],
        description=metadata["description"],
        image=metadata["image"],
        attributes=metadata["attributes"],
        metadata_url=metadata["metadata_url"],
    )


@router.get("/my-nfts", response_model=list[UserNFTResponse])
async def get_my_nfts(
    db: DBSession,
    current_user: CurrentUser,
) -> list[UserNFTResponse]:
    """Get all NFTs minted by current user.

    Args:
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of user's NFTs.
    """
    nfts = await nft_service.get_user_nfts(db, current_user.id)

    return [
        UserNFTResponse(
            nft_address=nft["nft_address"],
            transaction_hash=nft["transaction_hash"],
            minted_at=nft["minted_at"],
            result_id=nft["result_id"],
            metadata=(
                NFTMetadataResponse(
                    name=nft["metadata"]["name"],
                    description=nft["metadata"]["description"],
                    image=nft["metadata"]["image"],
                    attributes=nft["metadata"]["attributes"],
                    metadata_url=nft["metadata"]["metadata_url"],
                )
                if nft["metadata"]
                else None
            ),
        )
        for nft in nfts
    ]
