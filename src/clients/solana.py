"""Solana RPC Client — Zahlungsverifizierung on-chain."""

import httpx

from src.config import settings


class SolanaClient:
    """Minimaler Solana RPC Client für Payment-Verifizierung."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)

    async def _rpc(self, method: str, params: list) -> dict:
        """JSON-RPC Aufruf an Solana."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        resp = await self._client.post(settings.solana_rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Solana RPC Fehler: {data['error']}")
        return data.get("result", {})

    async def get_transaction(self, signature: str) -> dict:
        """Transaktionsdetails abrufen."""
        return await self._rpc("getTransaction", [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ])

    async def verify_usdc_transfer(
        self,
        signature: str,
        expected_recipient: str,
        expected_amount_usdc: float,
    ) -> dict:
        """Verifizieren ob eine USDC-Transaktion korrekt ist.

        Prüft: Empfänger, Betrag, Token (USDC), Bestätigung.
        """
        tx = await self.get_transaction(signature)
        if not tx:
            return {"verified": False, "reason": "Transaktion nicht gefunden"}

        # Transaktionsstatus prüfen
        meta = tx.get("meta", {})
        if meta.get("err"):
            return {"verified": False, "reason": f"Transaktion fehlgeschlagen: {meta['err']}"}

        # Token-Transfers suchen
        inner_instructions = meta.get("innerInstructions", [])
        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])

        # USDC-Transfers aus pre/post Token-Balances berechnen
        usdc_mint = settings.usdc_mint
        transfers = []

        # Alle Token-Balance-Änderungen durchgehen
        for post in post_balances:
            if post.get("mint") != usdc_mint:
                continue
            owner = post.get("owner", "")
            post_amount = float(post.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)

            # Vorherigen Balance finden
            pre_amount = 0
            for pre in pre_balances:
                if (pre.get("accountIndex") == post.get("accountIndex")
                        and pre.get("mint") == usdc_mint):
                    pre_amount = float(pre.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
                    break

            change = post_amount - pre_amount
            if change > 0:
                transfers.append({"recipient": owner, "amount": change})

        # Prüfen ob der erwartete Transfer dabei ist
        for t in transfers:
            if (t["recipient"] == expected_recipient
                    and abs(t["amount"] - expected_amount_usdc) < 0.001):
                return {
                    "verified": True,
                    "recipient": t["recipient"],
                    "amount_usdc": t["amount"],
                    "signature": signature,
                    "slot": tx.get("slot"),
                    "block_time": tx.get("blockTime"),
                }

        return {
            "verified": False,
            "reason": "Kein passender USDC-Transfer gefunden",
            "found_transfers": transfers,
        }

    async def get_balance(self, wallet: str) -> float:
        """SOL-Balance einer Wallet abrufen."""
        result = await self._rpc("getBalance", [wallet])
        lamports = result.get("value", 0)
        return lamports / 1_000_000_000  # Lamports → SOL

    async def close(self):
        await self._client.aclose()
