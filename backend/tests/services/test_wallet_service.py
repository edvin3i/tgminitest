"""Tests for TON wallet service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ton.wallet_service import WalletService


@pytest.fixture
def wallet_service() -> WalletService:
    """Create wallet service instance.

    Returns:
        WalletService instance.
    """
    return WalletService()


@pytest.fixture
def mock_wallet():
    """Create mock TON wallet.

    Returns:
        Mock wallet object.
    """
    wallet = MagicMock()
    wallet.address = MagicMock()
    wallet.address.to_str = MagicMock(return_value="EQD_test_wallet_address")
    return wallet


@pytest.fixture
def mock_tonapi():
    """Create mock TON API client.

    Returns:
        Mock AsyncTonapi object.
    """
    tonapi = AsyncMock()
    tonapi.accounts = AsyncMock()
    return tonapi


# ==================== Initialization Tests ====================


@pytest.mark.asyncio
async def test_initialize_with_valid_mnemonic(wallet_service: WalletService) -> None:
    """Test wallet initialization with valid mnemonic."""
    # Mock settings with valid mnemonic
    valid_mnemonic = " ".join(["word"] * 24)

    with patch("app.services.ton.wallet_service.settings") as mock_settings:
        mock_settings.TON_WALLET_MNEMONIC = valid_mnemonic
        mock_settings.TON_NETWORK = "testnet"
        mock_settings.TON_API_KEY = "test_key"

        mock_wallet = MagicMock()
        mock_wallet.address = MagicMock()
        mock_wallet.address.to_str = MagicMock(return_value="EQD_test_address")

        with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)):
            with patch("app.services.ton.wallet_service.AsyncTonapi") as mock_tonapi_class:
                wallet_service.mnemonic = valid_mnemonic.split()
                await wallet_service.initialize()

                assert wallet_service._wallet is not None
                assert wallet_service._tonapi is not None


@pytest.mark.asyncio
async def test_initialize_without_mnemonic(wallet_service: WalletService) -> None:
    """Test wallet initialization without mnemonic (should skip)."""
    wallet_service.mnemonic = []

    await wallet_service.initialize()

    # Should not initialize wallet
    assert wallet_service._wallet is None


@pytest.mark.asyncio
async def test_initialize_with_invalid_mnemonic(wallet_service: WalletService) -> None:
    """Test wallet initialization with invalid mnemonic length."""
    wallet_service.mnemonic = ["word"] * 12  # Only 12 words, need 24

    await wallet_service.initialize()

    # Should not initialize wallet
    assert wallet_service._wallet is None


@pytest.mark.asyncio
async def test_initialize_network_testnet(wallet_service: WalletService) -> None:
    """Test wallet initialization for testnet."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic
    wallet_service.network = "testnet"

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_testnet_address")

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)) as mock_from_mnemonic:
        with patch("app.services.ton.wallet_service.AsyncTonapi"):
            await wallet_service.initialize()

            # Verify testnet parameter was passed
            mock_from_mnemonic.assert_called_once()
            call_kwargs = mock_from_mnemonic.call_args[1]
            assert call_kwargs["testnet"] is True


@pytest.mark.asyncio
async def test_initialize_network_mainnet(wallet_service: WalletService) -> None:
    """Test wallet initialization for mainnet."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic
    wallet_service.network = "mainnet"

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_mainnet_address")

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)) as mock_from_mnemonic:
        with patch("app.services.ton.wallet_service.AsyncTonapi"):
            await wallet_service.initialize()

            # Verify mainnet parameter (testnet=False)
            mock_from_mnemonic.assert_called_once()
            call_kwargs = mock_from_mnemonic.call_args[1]
            assert call_kwargs["testnet"] is False


# ==================== Get Wallet Tests ====================


@pytest.mark.asyncio
async def test_get_wallet_already_initialized(wallet_service: WalletService, mock_wallet) -> None:
    """Test getting wallet when already initialized."""
    wallet_service._wallet = mock_wallet

    wallet = await wallet_service.get_wallet()

    assert wallet is mock_wallet


@pytest.mark.asyncio
async def test_get_wallet_not_initialized(wallet_service: WalletService) -> None:
    """Test getting wallet when not initialized (should initialize)."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_address")

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)):
        with patch("app.services.ton.wallet_service.AsyncTonapi"):
            wallet = await wallet_service.get_wallet()

            assert wallet is not None


@pytest.mark.asyncio
async def test_get_wallet_initialization_fails(wallet_service: WalletService) -> None:
    """Test getting wallet when initialization fails."""
    wallet_service.mnemonic = []  # Invalid mnemonic

    with pytest.raises(RuntimeError, match="Wallet not initialized"):
        await wallet_service.get_wallet()


# ==================== Get Address Tests ====================


@pytest.mark.asyncio
async def test_get_address(wallet_service: WalletService, mock_wallet) -> None:
    """Test getting wallet address."""
    wallet_service._wallet = mock_wallet

    address = await wallet_service.get_address()

    assert address == "EQD_test_wallet_address"
    mock_wallet.address.to_str.assert_called_once_with(is_bounceable=False)


@pytest.mark.asyncio
async def test_get_address_non_bounceable(wallet_service: WalletService, mock_wallet) -> None:
    """Test that address is returned in non-bounceable format."""
    wallet_service._wallet = mock_wallet

    await wallet_service.get_address()

    # Verify non-bounceable format is requested
    mock_wallet.address.to_str.assert_called_with(is_bounceable=False)


# ==================== Get Balance Tests ====================


@pytest.mark.asyncio
async def test_get_balance_success(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test getting wallet balance successfully."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    # Mock account info with balance in nanotons
    mock_account = MagicMock()
    mock_account.balance = 5_000_000_000  # 5 TON in nanotons
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    balance = await wallet_service.get_balance()

    assert balance == 5.0
    mock_tonapi.accounts.get_info.assert_called_once_with("EQD_test_wallet_address")


@pytest.mark.asyncio
async def test_get_balance_zero(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test getting zero balance."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 0
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    balance = await wallet_service.get_balance()

    assert balance == 0.0


@pytest.mark.asyncio
async def test_get_balance_large_amount(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test getting large balance."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 1_234_567_890_123  # Large amount
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    balance = await wallet_service.get_balance()

    # Should convert nanotons to TON correctly
    assert balance == pytest.approx(1234.567890123, rel=1e-9)


@pytest.mark.asyncio
async def test_get_balance_not_initialized(wallet_service: WalletService) -> None:
    """Test getting balance when wallet not initialized."""
    wallet_service._tonapi = None
    wallet_service.mnemonic = []

    with pytest.raises(RuntimeError):
        await wallet_service.get_balance()


# ==================== Check Balance Tests ====================


@pytest.mark.asyncio
async def test_check_balance_sufficient(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test checking balance when sufficient."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 1_000_000_000  # 1 TON
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    is_sufficient = await wallet_service.check_balance(min_balance=0.5)

    assert is_sufficient is True


@pytest.mark.asyncio
async def test_check_balance_insufficient(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test checking balance when insufficient."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 50_000_000  # 0.05 TON
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    is_sufficient = await wallet_service.check_balance(min_balance=0.1)

    assert is_sufficient is False


@pytest.mark.asyncio
async def test_check_balance_exact(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test checking balance when exactly at minimum."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 100_000_000  # 0.1 TON
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    is_sufficient = await wallet_service.check_balance(min_balance=0.1)

    assert is_sufficient is True


@pytest.mark.asyncio
async def test_check_balance_error_handling(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test that check_balance handles errors gracefully."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_tonapi.accounts.get_info = AsyncMock(side_effect=Exception("Network error"))

    # Should return False on error, not raise
    is_sufficient = await wallet_service.check_balance()

    assert is_sufficient is False


# ==================== Get Seqno Tests ====================


@pytest.mark.asyncio
async def test_get_seqno(wallet_service: WalletService, mock_wallet) -> None:
    """Test getting wallet seqno (placeholder implementation)."""
    wallet_service._wallet = mock_wallet

    seqno = await wallet_service.get_seqno()

    # Currently returns 0 as placeholder
    assert seqno == 0


# ==================== Get Account State Tests ====================


@pytest.mark.asyncio
async def test_get_account_state_active(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test getting account state for active account."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 1_000_000_000
    mock_account.status = "active"
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    state = await wallet_service.get_account_state()

    assert state["address"] == "EQD_test_wallet_address"
    assert state["balance"] == 1.0
    assert state["status"] == "active"
    assert state["is_active"] is True


@pytest.mark.asyncio
async def test_get_account_state_uninit(wallet_service: WalletService, mock_wallet, mock_tonapi) -> None:
    """Test getting account state for uninitialized account."""
    wallet_service._wallet = mock_wallet
    wallet_service._tonapi = mock_tonapi

    mock_account = MagicMock()
    mock_account.balance = 0
    mock_account.status = "uninit"
    mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)

    state = await wallet_service.get_account_state()

    assert state["status"] == "uninit"
    assert state["is_active"] is False


# ==================== Health Check Tests ====================


@pytest.mark.asyncio
async def test_health_check_healthy(wallet_service: WalletService) -> None:
    """Test health check for healthy wallet."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic
    wallet_service.network = "testnet"

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_healthy_wallet")

    mock_account = MagicMock()
    mock_account.balance = 100_000_000  # 0.1 TON
    mock_account.status = "active"

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)):
        with patch("app.services.ton.wallet_service.AsyncTonapi") as mock_tonapi_class:
            mock_tonapi = AsyncMock()
            mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)
            mock_tonapi_class.return_value = mock_tonapi

            health = await wallet_service.health_check()

            assert health["healthy"] is True
            assert health["balance"] == 0.1
            assert health["address"] == "EQD_healthy_wallet"
            assert health["network"] == "testnet"
            assert health["status"] == "active"


@pytest.mark.asyncio
async def test_health_check_low_balance(wallet_service: WalletService) -> None:
    """Test health check with low balance."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_low_balance")

    mock_account = MagicMock()
    mock_account.balance = 10_000_000  # 0.01 TON (below 0.05 threshold)
    mock_account.status = "active"

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)):
        with patch("app.services.ton.wallet_service.AsyncTonapi") as mock_tonapi_class:
            mock_tonapi = AsyncMock()
            mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)
            mock_tonapi_class.return_value = mock_tonapi

            health = await wallet_service.health_check()

            assert health["healthy"] is False  # Below minimum threshold


@pytest.mark.asyncio
async def test_health_check_inactive_account(wallet_service: WalletService) -> None:
    """Test health check with inactive account."""
    valid_mnemonic = ["word"] * 24
    wallet_service.mnemonic = valid_mnemonic

    mock_wallet = MagicMock()
    mock_wallet.address = MagicMock()
    mock_wallet.address.to_str = MagicMock(return_value="EQD_inactive")

    mock_account = MagicMock()
    mock_account.balance = 100_000_000  # 0.1 TON
    mock_account.status = "uninit"

    with patch("app.services.ton.wallet_service.WalletV4R2.from_mnemonic", new=AsyncMock(return_value=mock_wallet)):
        with patch("app.services.ton.wallet_service.AsyncTonapi") as mock_tonapi_class:
            mock_tonapi = AsyncMock()
            mock_tonapi.accounts.get_info = AsyncMock(return_value=mock_account)
            mock_tonapi_class.return_value = mock_tonapi

            health = await wallet_service.health_check()

            assert health["healthy"] is False  # Inactive account


@pytest.mark.asyncio
async def test_health_check_error(wallet_service: WalletService) -> None:
    """Test health check when error occurs."""
    wallet_service.mnemonic = []  # Will cause initialization failure

    health = await wallet_service.health_check()

    assert health["healthy"] is False
    assert "error" in health


# ==================== Close Tests ====================


@pytest.mark.asyncio
async def test_close_with_tonapi(wallet_service: WalletService, mock_tonapi) -> None:
    """Test closing TON API client."""
    wallet_service._tonapi = mock_tonapi
    mock_tonapi.close = AsyncMock()

    await wallet_service.close()

    mock_tonapi.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_without_tonapi(wallet_service: WalletService) -> None:
    """Test closing when TON API client not initialized."""
    wallet_service._tonapi = None

    # Should not raise
    await wallet_service.close()


# ==================== Service Configuration Tests ====================


def test_service_initialization_defaults(wallet_service: WalletService) -> None:
    """Test that service initializes with correct defaults."""
    assert hasattr(wallet_service, "network")
    assert hasattr(wallet_service, "mnemonic")
    assert hasattr(wallet_service, "api_key")
    assert wallet_service._wallet is None
    assert wallet_service._tonapi is None
