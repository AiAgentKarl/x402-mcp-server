# x402 Payment Gateway MCP Server 💰

MCP Server that enables **micropayments between AI agents** using USDC on Solana. Based on the [x402 protocol](https://www.x402.org/) (HTTP 402 Payment Required).

## What is x402?

x402 is a protocol that lets AI agents pay for services automatically. When an agent calls a premium tool, it gets a "402 Payment Required" response with payment instructions. The agent pays via blockchain, then gets access.

## Features

- **Payment Requests** — Create x402-compatible payment requests for any tool
- **On-Chain Verification** — Verify USDC payments directly on Solana
- **Tool Pricing** — Set per-call prices for individual tools
- **Revenue Tracking** — Dashboard with total revenue, per-tool breakdown
- **Payment History** — Full audit trail of all transactions

## Installation

```bash
pip install x402-mcp-server
```

## Configuration

Set your merchant wallet in `.env`:

```env
MERCHANT_WALLET=YourSolanaWalletAddress
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

## Usage with Claude Code

```json
{
  "mcpServers": {
    "x402": {
      "command": "uvx",
      "args": ["x402-mcp-server"],
      "env": {
        "MERCHANT_WALLET": "YourSolanaWalletAddress"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `create_payment_request` | Create a 402 payment request for a tool |
| `verify_payment` | Verify on-chain USDC payment |
| `get_payment_status` | Check payment status |
| `set_tool_price` | Set price for a tool |
| `get_price_list` | View all tool prices |
| `list_payments` | Payment history |
| `get_revenue` | Revenue statistics |

## Flow

```
Agent A                    x402 Gateway                 Agent B (Service)
   |                           |                             |
   |-- "Use premium tool" ---->|                             |
   |                           |-- 402 Payment Required ---->|
   |<-- Payment instructions --|                             |
   |                           |                             |
   |-- USDC payment on-chain ->|                             |
   |                           |-- verify_payment ---------->|
   |                           |<-- verified ----------------|
   |<-- Access granted --------|                             |
```


---

## More MCP Servers by AiAgentKarl

| Category | Servers |
|----------|---------|
| 🔗 Blockchain | [Solana](https://github.com/AiAgentKarl/solana-mcp-server) |
| 🌍 Data | [Weather](https://github.com/AiAgentKarl/weather-mcp-server) · [Germany](https://github.com/AiAgentKarl/germany-mcp-server) · [Agriculture](https://github.com/AiAgentKarl/agriculture-mcp-server) · [Space](https://github.com/AiAgentKarl/space-mcp-server) · [Aviation](https://github.com/AiAgentKarl/aviation-mcp-server) · [EU Companies](https://github.com/AiAgentKarl/eu-company-mcp-server) |
| 🔒 Security | [Cybersecurity](https://github.com/AiAgentKarl/cybersecurity-mcp-server) · [Policy Gateway](https://github.com/AiAgentKarl/agent-policy-gateway-mcp) · [Audit Trail](https://github.com/AiAgentKarl/agent-audit-trail-mcp) |
| 🤖 Agent Infra | [Memory](https://github.com/AiAgentKarl/agent-memory-mcp-server) · [Directory](https://github.com/AiAgentKarl/agent-directory-mcp-server) · [Hub](https://github.com/AiAgentKarl/mcp-appstore-server) · [Reputation](https://github.com/AiAgentKarl/agent-reputation-mcp-server) |
| 🔬 Research | [Academic](https://github.com/AiAgentKarl/crossref-academic-mcp-server) · [LLM Benchmark](https://github.com/AiAgentKarl/llm-benchmark-mcp-server) · [Legal](https://github.com/AiAgentKarl/legal-court-mcp-server) |

[→ Full catalog (40+ servers)](https://github.com/AiAgentKarl)

## License

MIT
