"""TON wallet service for managing minting wallet and transactions."""

from typing import Any

from loguru import logger
from pytonapi import AsyncTonapi
from pytoniq_core import Address
from pytoniq_tools import WalletV4R2

from app.config import settings


class WalletService:
    """Service for TON wallet operations and balance management."""

    def __init__(self) -> None:
        """Initialize WalletService with configuration."""
        self.network = settings.TON_NETWORK
        self.mnemonic = settings.TON_WALLET_MNEMONIC.split() if settings.TON_WALLET_MNEMONIC else []
        self.api_key = settings.TON_API_KEY
        self._wallet: WalletV4R2 | None = None
        self._tonapi: AsyncTonapi | None = None

    async def initialize(self) -> None:
        """Initialize wallet and TON API client."""
        try:
            if not self.mnemonic or len(self.mnemonic) != 24:
                logger.warning("TON wallet mnemonic not configured or invalid")
                return

            # Initialize wallet from mnemonic
            self._wallet = await WalletV4R2.from_mnemonic(
                mnemonic=self.mnemonic,
                testnet=self.network == "testnet",
            )

            # Initialize TON API client
            self._tonapi = AsyncTonapi(
                api_key=self.api_key,
                is_testnet=self.network == "testnet",
            )

            wallet_address = self._wallet.address.to_str(is_bounceable=False)
            logger.info(f"TON wallet initialized: {wallet_address}")

        except Exception as e:
            logger.exception(f"Error initializing TON wallet: {e}")
            raise

    async def get_wallet(self) -> WalletV4R2:
        """Get initialized wallet instance.

        Returns:
            Wallet instance.

        Raises:
            RuntimeError: If wallet not initialized.
        """
        if self._wallet is None:
            await self.initialize()
            if self._wallet is None:
                raise RuntimeError("Wallet not initialized. Check mnemonic configuration.")
        return self._wallet

    async def get_address(self) -> str:
        """Get wallet address as string.

        Returns:
            Wallet address (non-bounceable format).
        """
        wallet = await self.get_wallet()
        return wallet.address.to_str(is_bounceable=False)

    async def get_balance(self) -> float:
        """Get wallet balance in TON.

        Returns:
            Balance in TON (not nanoton).

        Raises:
            Exception: If balance check fails.
        """
        try:
            if self._tonapi is None:
                await self.initialize()

            wallet_address = await self.get_address()

            # Get account info from TonAPI
            account = await self._tonapi.accounts.get_info(wallet_address)
            balance_nanoton = account.balance

            # Convert nanoton to TON
            balance_ton = balance_nanoton / 1_000_000_000

            logger.debug(f"Wallet balance: {balance_ton} TON")
            return balance_ton

        except Exception as e:
            logger.exception(f"Error getting wallet balance: {e}")
            raise

    async def check_balance(self, min_balance: float = 0.1) -> bool:
        """Check if wallet has sufficient balance.

        Args:
            min_balance: Minimum required balance in TON.

        Returns:
            True if balance is sufficient, False otherwise.
        """
        try:
            balance = await self.get_balance()
            is_sufficient = balance >= min_balance

            if not is_sufficient:
                logger.warning(
                    f"Low wallet balance: {balance} TON (minimum: {min_balance} TON)"
                )

            return is_sufficient

        except Exception as e:
            logger.error(f"Error checking wallet balance: {e}")
            return False

    async def get_seqno(self) -> int:
        """Get current wallet sequence number.

        Returns:
            Current seqno.

        Raises:
            Exception: If seqno fetch fails.
        """
        try:
            wallet = await self.get_wallet()
            # This will be implemented when we integrate with blockchain
            # For now, return 0 as placeholder
            logger.debug("Getting wallet seqno (placeholder)")
            return 0

        except Exception as e:
            logger.error(f"Error getting wallet seqno: {e}")
            raise

    async def get_account_state(self) -> dict[str, Any]:
        """Get full account state from TonAPI.

        Returns:
            Account state dictionary.
        """
        try:
            if self._tonapi is None:
                await self.initialize()

            wallet_address = await self.get_address()
            account = await self._tonapi.accounts.get_info(wallet_address)

            return {
                "address": wallet_address,
                "balance": account.balance / 1_000_000_000,  # Convert to TON
                "status": account.status,
                "is_active": account.status == "active",
            }

        except Exception as e:
            logger.exception(f"Error getting account state: {e}")
            raise

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on wallet.

        Returns:
            Health check results.
        """
        try:
            await self.initialize()

            balance = await self.get_balance()
            state = await self.get_account_state()

            is_healthy = (
                balance > 0.05  # Minimum 0.05 TON
                and state["is_active"]
            )

            return {
                "healthy": is_healthy,
                "balance": balance,
                "address": await self.get_address(),
                "network": self.network,
                "status": state["status"],
            }

        except Exception as e:
            logger.exception(f"Wallet health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close TON API client connection."""
        if self._tonapi:
            await self._tonapi.close()
            logger.info("TON API client closed")


# Global instance
wallet_service = WalletService()
