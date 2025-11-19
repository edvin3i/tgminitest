"""Tests for NFT API endpoints."""

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.quiz import Answer, Question, Quiz, ResultType
from app.models.result import MintTransaction, Payment, QuizResult
from app.models.user import User


def override_get_current_user(test_user: User):
    """Override get_current_user dependency for tests."""
    async def _get_current_user() -> User:
        return test_user
    return _get_current_user


def override_get_db(db_session: AsyncSession):
    """Override get_db dependency for tests."""
    async def _get_db():
        yield db_session
    return _get_db


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Create async HTTP client for API testing.

    Returns:
        AsyncClient: HTTP client instance.
    """
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_quiz(db_session: AsyncSession, admin_user: User) -> Quiz:
    """Create a test quiz with questions and answers."""
    quiz = Quiz(
        title="Test Quiz",
        description="A test quiz",
        is_active=True,
        created_by=admin_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    question = Question(
        quiz_id=quiz.id,
        text="Test question?",
        order_index=0,
    )
    db_session.add(question)
    await db_session.flush()

    answer = Answer(
        question_id=question.id,
        text="Test answer",
        result_type="test_result",
        weight=1,
        order_index=0,
    )
    db_session.add(answer)

    result_type = ResultType(
        quiz_id=quiz.id,
        type_key="test_result",
        title="Test Result",
        description="A test result",
    )
    db_session.add(result_type)

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest_asyncio.fixture
async def test_quiz_result(
    db_session: AsyncSession,
    test_user: User,
    test_quiz: Quiz,
) -> QuizResult:
    """Create a test quiz result."""
    quiz_result = QuizResult(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        answers_data={"1": 1},
        result_type="test_result",
        score=10,
        nft_minted=False,
    )
    db_session.add(quiz_result)
    await db_session.commit()
    await db_session.refresh(quiz_result)
    return quiz_result


@pytest.mark.asyncio
async def test_initiate_nft_mint_unauthorized(
    client: AsyncClient,
) -> None:
    """Test that initiating NFT mint without auth fails."""
    response = await client.post(
        "/api/v1/nft/mint",
        json={"result_id": 1, "provider": "telegram_stars"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_initiate_nft_mint_success(
    client: AsyncClient,
    test_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test successful NFT mint initiation."""
    # Override dependencies
    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.post(
            "/api/v1/nft/mint",
            json={
                "result_id": test_quiz_result.id,
                "provider": "telegram_stars",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["result_id"] == test_quiz_result.id
        assert data["currency"] == "STARS"
        assert data["status"] == "pending"
        assert "invoice_data" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_initiate_nft_mint_invalid_result(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """Test NFT mint initiation with invalid result ID."""
    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.post(
            "/api/v1/nft/mint",
            json={
                "result_id": 99999,  # Non-existent
                "provider": "telegram_stars",
            },
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_mint_status_unauthorized(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test getting mint status without auth fails."""
    # Override db dependency (even for unauthenticated tests)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.get("/api/v1/nft/status/1")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_mint_status_success(
    client: AsyncClient,
    test_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test getting mint transaction status."""
    # Create mint transaction
    mint_tx = MintTransaction(
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        status="pending",
    )
    db_session.add(mint_tx)
    await db_session.commit()
    await db_session.refresh(mint_tx)

    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.get(
            f"/api/v1/nft/status/{mint_tx.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == mint_tx.id
        assert data["status"] == "pending"
        assert data["result_id"] == test_quiz_result.id
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_mint_status_wrong_user(
    client: AsyncClient,
    test_user: User,
    admin_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test getting mint status for another user's transaction fails."""
    # Create mint transaction for test_user
    mint_tx = MintTransaction(
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        status="pending",
    )
    db_session.add(mint_tx)
    await db_session.commit()

    # Try to access with admin_user
    app.dependency_overrides[get_current_user] = override_get_current_user(admin_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.get(
            f"/api/v1/nft/status/{mint_tx.id}",
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_my_nfts_unauthorized(
    client: AsyncClient,
) -> None:
    """Test getting user's NFTs without auth fails."""
    response = await client.get("/api/v1/nft/my-nfts")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_nfts_empty(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """Test getting NFTs when user has none."""
    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.get(
            "/api/v1/nft/my-nfts",
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_my_nfts_with_nfts(
    client: AsyncClient,
    test_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test getting NFTs when user has minted NFTs."""
    # Create completed mint transaction
    mint_tx = MintTransaction(
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        status="completed",
        nft_address="EQD...test123",
        transaction_hash="tx_hash_123",
        ipfs_hash="ipfs_hash_456",
    )
    db_session.add(mint_tx)

    # Mark result as minted
    test_quiz_result.nft_minted = True
    test_quiz_result.nft_address = "EQD...test123"

    await db_session.commit()

    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.get(
            "/api/v1/nft/my-nfts",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nft_address"] == "EQD...test123"
        assert data[0]["result_id"] == test_quiz_result.id
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_confirm_mint_payment_unauthorized(
    client: AsyncClient,
) -> None:
    """Test confirming payment without auth fails."""
    response = await client.post(
        "/api/v1/nft/mint/confirm",
        json={"payment_id": 1},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirm_mint_payment_not_paid(
    client: AsyncClient,
    test_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test confirming unpaid payment fails."""
    # Create pending payment
    payment = Payment(
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        amount=10,
        currency="STARS",
        status="pending",
        provider="telegram_stars",
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    app.dependency_overrides[get_current_user] = override_get_current_user(test_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.post(
            "/api/v1/nft/mint/confirm",
            json={"payment_id": payment.id},
        )

        assert response.status_code == 400
        assert "expected 'paid'" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_confirm_mint_payment_wrong_user(
    client: AsyncClient,
    test_user: User,
    admin_user: User,
    test_quiz_result: QuizResult,
    db_session: AsyncSession,
) -> None:
    """Test confirming another user's payment fails."""
    # Create paid payment for test_user
    payment = Payment(
        user_id=test_user.id,
        result_id=test_quiz_result.id,
        amount=10,
        currency="STARS",
        status="paid",
        provider="telegram_stars",
    )
    db_session.add(payment)
    await db_session.commit()

    # Try to confirm with admin_user
    app.dependency_overrides[get_current_user] = override_get_current_user(admin_user)
    app.dependency_overrides[get_db] = override_get_db(db_session)

    try:
        response = await client.post(
            "/api/v1/nft/mint/confirm",
            json={"payment_id": payment.id},
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
