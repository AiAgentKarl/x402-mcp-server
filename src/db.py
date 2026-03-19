"""Datenbank — SQLite-basiertes Payment-Tracking."""

import sqlite3
import uuid
from datetime import datetime, timezone

from src.config import settings


def _connect() -> sqlite3.Connection:
    """DB-Verbindung herstellen und Schema anlegen."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            service_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            amount_usdc REAL NOT NULL,
            payer_wallet TEXT,
            merchant_wallet TEXT NOT NULL,
            tx_signature TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            verified_at TEXT,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_list (
            service_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            price_usdc REAL NOT NULL,
            description TEXT,
            PRIMARY KEY (service_id, tool_name)
        )
    """)
    conn.commit()
    return conn


def create_payment(
    service_id: str,
    tool_name: str,
    amount_usdc: float,
    merchant_wallet: str,
    payer_wallet: str = None,
    metadata: str = None,
) -> dict:
    """Neuen Payment-Request erstellen."""
    conn = _connect()
    payment_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO payments
           (id, service_id, tool_name, amount_usdc, payer_wallet,
            merchant_wallet, status, created_at, metadata)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
        (payment_id, service_id, tool_name, amount_usdc,
         payer_wallet, merchant_wallet, now, metadata),
    )
    conn.commit()
    conn.close()
    return {
        "payment_id": payment_id,
        "amount_usdc": amount_usdc,
        "merchant_wallet": merchant_wallet,
        "status": "pending",
        "created_at": now,
    }


def verify_payment(payment_id: str, tx_signature: str) -> dict:
    """Payment als verifiziert markieren."""
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE payments SET status='verified', tx_signature=?, verified_at=?
           WHERE id=?""",
        (tx_signature, now, payment_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"error": f"Payment {payment_id} nicht gefunden"}


def get_payment(payment_id: str) -> dict | None:
    """Payment-Details abrufen."""
    conn = _connect()
    row = conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_payments(service_id: str = None, status: str = None, limit: int = 50) -> list:
    """Payments auflisten mit optionalen Filtern."""
    conn = _connect()
    query = "SELECT * FROM payments WHERE 1=1"
    params = []
    if service_id:
        query += " AND service_id=?"
        params.append(service_id)
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_price(service_id: str, tool_name: str, price_usdc: float, description: str = "") -> dict:
    """Preis für ein Tool festlegen."""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO price_list (service_id, tool_name, price_usdc, description)
           VALUES (?, ?, ?, ?)""",
        (service_id, tool_name, price_usdc, description),
    )
    conn.commit()
    conn.close()
    return {"service_id": service_id, "tool_name": tool_name, "price_usdc": price_usdc}


def get_price(service_id: str, tool_name: str) -> dict | None:
    """Preis für ein Tool abrufen."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM price_list WHERE service_id=? AND tool_name=?",
        (service_id, tool_name),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_price_list(service_id: str = None) -> list:
    """Alle Preise auflisten."""
    conn = _connect()
    if service_id:
        rows = conn.execute(
            "SELECT * FROM price_list WHERE service_id=?", (service_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM price_list").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_revenue_stats(service_id: str = None) -> dict:
    """Umsatzstatistiken abrufen."""
    conn = _connect()
    query = "SELECT * FROM payments WHERE status='verified'"
    params = []
    if service_id:
        query += " AND service_id=?"
        params.append(service_id)
    rows = conn.execute(query, params).fetchall()
    conn.close()

    total = sum(r["amount_usdc"] for r in rows)
    by_tool = {}
    for r in rows:
        tool = r["tool_name"]
        by_tool[tool] = by_tool.get(tool, 0) + r["amount_usdc"]

    return {
        "total_revenue_usdc": round(total, 6),
        "total_transactions": len(rows),
        "revenue_by_tool": by_tool,
    }
