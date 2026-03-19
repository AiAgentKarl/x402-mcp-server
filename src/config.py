"""Konfiguration — x402 Payment Gateway Settings."""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# .env oder keys.env laden
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / "keys.env"
if not _env_path.exists():
    _env_path = _project_root / ".env"
load_dotenv(_env_path)


class Settings(BaseModel):
    """Zentrale Konfiguration für x402 Payment Gateway."""

    # Empfänger-Wallet für Zahlungen (USDC auf Solana)
    merchant_wallet: str = os.getenv("MERCHANT_WALLET", "")

    # Solana RPC (Helius oder öffentlich)
    solana_rpc_url: str = os.getenv(
        "SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"
    )

    # USDC Mint auf Solana
    usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    # Lokale Datenbank für Payment-Tracking
    db_path: str = str(_project_root / "payments.db")

    # HTTP-Client Defaults
    http_timeout: float = 30.0


# Globale Settings-Instanz
settings = Settings()
