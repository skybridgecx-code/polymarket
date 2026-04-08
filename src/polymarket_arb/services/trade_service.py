from __future__ import annotations

from typing import Any

from polymarket_arb.config import Settings


class TradeService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _build_clob_client(self):
        from py_clob_client.client import ClobClient as PyClobClient
        from py_clob_client.clob_types import ApiCreds

        s = self._settings
        if not s.poly_private_key:
            raise RuntimeError("POLY_PRIVATE_KEY is not set in .env")
        if not s.poly_api_key or not s.poly_api_secret or not s.poly_passphrase:
            raise RuntimeError(
                "POLY_API_KEY, POLY_API_SECRET, and POLY_PASSPHRASE must all be set in .env"
            )

        creds = ApiCreds(
            api_key=s.poly_api_key,
            api_secret=s.poly_api_secret,
            api_passphrase=s.poly_passphrase,
        )
        client = PyClobClient(
            str(s.clob_base_url),
            chain_id=s.poly_chain_id,
            key=s.poly_private_key,
            creds=creds,
        )
        return client

    def derive_api_credentials(self) -> dict[str, Any]:
        """Derive API credentials from private key. Run this once to get your API key/secret/passphrase."""
        from py_clob_client.client import ClobClient as PyClobClient

        s = self._settings
        if not s.poly_private_key:
            raise RuntimeError("POLY_PRIVATE_KEY is not set in .env")

        client = PyClobClient(
            str(s.clob_base_url),
            chain_id=s.poly_chain_id,
            key=s.poly_private_key,
        )
        creds = client.create_or_derive_api_creds()
        return {
            "api_key": creds.api_key,
            "api_secret": creds.api_secret,
            "api_passphrase": creds.api_passphrase,
            "status": "success",
            "message": "Add these to your .env file as POLY_API_KEY, POLY_API_SECRET, POLY_PASSPHRASE",
        }

    def get_balance(self) -> dict[str, Any]:
        """Check USDC balance and allowance."""
        client = self._build_clob_client()
        balance = client.get_balance_allowance()
        return {
            "balance": balance,
            "status": "success",
        }

    def buy(self, *, token_id: str, price: float, size: float) -> dict[str, Any]:
        """Place a limit buy order."""
        from py_clob_client.clob_types import OrderArgs
        from py_clob_client.order_builder.constants import BUY

        if price <= 0 or price >= 1:
            raise ValueError("Price must be between 0 and 1 (exclusive)")
        if size <= 0:
            raise ValueError("Size must be positive")
        if size > 100:
            raise ValueError("Size cannot exceed 100 shares (safety limit)")

        client = self._build_clob_client()
        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=BUY,
        )
        result = client.create_and_post_order(order_args)
        return {
            "action": "buy",
            "token_id": token_id,
            "price": price,
            "size": size,
            "result": result,
            "status": "submitted",
        }

    def get_open_orders(self) -> dict[str, Any]:
        """Get all open orders."""
        client = self._build_clob_client()
        orders = client.get_orders()
        return {
            "orders": orders,
            "status": "success",
        }

    def cancel_all_orders(self) -> dict[str, Any]:
        """Cancel all open orders."""
        client = self._build_clob_client()
        result = client.cancel_all()
        return {
            "result": result,
            "status": "success",
        }
