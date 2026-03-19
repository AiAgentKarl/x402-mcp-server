"""x402 Payment Gateway MCP Server — Micropayments zwischen AI-Agents."""

from mcp.server.fastmcp import FastMCP

from src.tools.payments import register_payment_tools

mcp = FastMCP(
    "x402 Payment Gateway",
    instructions=(
        "Enables micropayments between AI agents using USDC on Solana. "
        "Create payment requests, verify on-chain transactions, "
        "manage tool pricing, and track revenue. "
        "Based on the x402 (HTTP 402 Payment Required) protocol."
    ),
)

register_payment_tools(mcp)


def main():
    """Server starten."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
