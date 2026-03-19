"""Payment-Tools — x402 Micropayments zwischen AI-Agents."""

from mcp.server.fastmcp import FastMCP

from src.clients.solana import SolanaClient
from src.config import settings
from src import db

_solana = SolanaClient()


def register_payment_tools(mcp: FastMCP):
    """Payment-bezogene MCP-Tools registrieren."""

    @mcp.tool()
    async def create_payment_request(
        tool_name: str,
        amount_usdc: float,
        service_id: str = "default",
        payer_wallet: str = None,
        description: str = None,
    ) -> dict:
        """x402 Payment Request erstellen.

        Erstellt eine Zahlungsaufforderung die ein Agent bezahlen muss,
        bevor er Zugriff auf ein Premium-Tool bekommt.

        Args:
            tool_name: Name des Tools das bezahlt werden soll
            amount_usdc: Preis in USDC (z.B. 0.01 für 1 Cent)
            service_id: ID des Service-Anbieters (Standard: "default")
            payer_wallet: Wallet des Zahlenden (optional)
            description: Beschreibung wofür bezahlt wird
        """
        merchant = settings.merchant_wallet
        if not merchant:
            return {"error": "Keine Merchant-Wallet konfiguriert (MERCHANT_WALLET in .env setzen)"}

        payment = db.create_payment(
            service_id=service_id,
            tool_name=tool_name,
            amount_usdc=amount_usdc,
            merchant_wallet=merchant,
            payer_wallet=payer_wallet,
            metadata=description,
        )

        return {
            "status": "402_payment_required",
            "payment_id": payment["payment_id"],
            "amount_usdc": amount_usdc,
            "currency": "USDC",
            "network": "solana",
            "recipient_wallet": merchant,
            "usdc_mint": settings.usdc_mint,
            "instructions": (
                f"Sende {amount_usdc} USDC an {merchant} auf Solana. "
                f"Dann rufe verify_payment mit der TX-Signatur und "
                f"payment_id='{payment['payment_id']}' auf."
            ),
        }

    @mcp.tool()
    async def verify_payment(payment_id: str, tx_signature: str) -> dict:
        """On-Chain Zahlung verifizieren.

        Prüft ob eine USDC-Transaktion auf Solana korrekt durchgeführt wurde:
        richtiger Empfänger, richtiger Betrag, bestätigt on-chain.

        Args:
            payment_id: Payment-ID aus create_payment_request
            tx_signature: Solana-Transaktions-Signatur
        """
        # Payment aus DB laden
        payment = db.get_payment(payment_id)
        if not payment:
            return {"verified": False, "error": f"Payment {payment_id} nicht gefunden"}

        if payment["status"] == "verified":
            return {
                "verified": True,
                "message": "Zahlung wurde bereits verifiziert",
                "payment": payment,
            }

        # On-Chain verifizieren
        result = await _solana.verify_usdc_transfer(
            signature=tx_signature,
            expected_recipient=payment["merchant_wallet"],
            expected_amount_usdc=payment["amount_usdc"],
        )

        if result["verified"]:
            # Payment als verifiziert markieren
            updated = db.verify_payment(payment_id, tx_signature)
            return {
                "verified": True,
                "message": "Zahlung erfolgreich verifiziert!",
                "payment": updated,
                "on_chain": result,
            }
        else:
            return {
                "verified": False,
                "reason": result.get("reason", "Verifizierung fehlgeschlagen"),
                "payment_id": payment_id,
            }

    @mcp.tool()
    async def get_payment_status(payment_id: str) -> dict:
        """Status einer Zahlung abfragen.

        Args:
            payment_id: Payment-ID aus create_payment_request
        """
        payment = db.get_payment(payment_id)
        if not payment:
            return {"error": f"Payment {payment_id} nicht gefunden"}
        return payment

    @mcp.tool()
    async def set_tool_price(
        tool_name: str,
        price_usdc: float,
        service_id: str = "default",
        description: str = "",
    ) -> dict:
        """Preis für ein Tool festlegen.

        Definiert wie viel USDC ein Agent für die Nutzung
        eines bestimmten Tools bezahlen muss.

        Args:
            tool_name: Name des Tools
            price_usdc: Preis in USDC pro Aufruf
            service_id: ID des Service-Anbieters
            description: Beschreibung des Tools
        """
        return db.set_price(service_id, tool_name, price_usdc, description)

    @mcp.tool()
    async def get_price_list(service_id: str = None) -> dict:
        """Preisliste aller Tools abrufen.

        Zeigt alle konfigurierten Preise für Tools an.

        Args:
            service_id: Optional — nur Preise für diesen Service
        """
        prices = db.get_price_list(service_id)
        return {
            "total_tools": len(prices),
            "prices": prices,
        }

    @mcp.tool()
    async def list_payments(
        service_id: str = None,
        status: str = None,
        limit: int = 20,
    ) -> dict:
        """Zahlungshistorie abrufen.

        Listet alle Zahlungen auf, optional gefiltert nach Service oder Status.

        Args:
            service_id: Optional — nur Zahlungen für diesen Service
            status: Optional — "pending" oder "verified"
            limit: Maximale Anzahl (Standard: 20)
        """
        payments = db.list_payments(service_id, status, limit)
        return {
            "total": len(payments),
            "payments": payments,
        }

    @mcp.tool()
    async def get_revenue(service_id: str = None) -> dict:
        """Umsatzstatistiken abrufen.

        Zeigt Gesamtumsatz, Anzahl Transaktionen und Umsatz pro Tool.

        Args:
            service_id: Optional — nur Umsatz für diesen Service
        """
        return db.get_revenue_stats(service_id)
