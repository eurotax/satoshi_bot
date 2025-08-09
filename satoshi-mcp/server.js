import express from "express";
import axios from "axios";
import { Server, HttpServerTransport } from "@modelcontextprotocol/sdk/server/http";

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || "";
const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;

const app = express();
app.use(express.json());

// Health/keep-alive
app.get("/", (_req, res) => res.status(200).send("Satoshi MCP: OK"));
app.get("/health", (_req, res) => res.status(200).json({ ok: true }));

// MCP tools
const tools = [
  {
    name: "dexscreener_pair",
    description:
      "Fetch pair info from DexScreener by chain and pair address. Returns price, liquidity, fdv, volume, priceChange.",
    inputSchema: {
      type: "object",
      properties: {
        chainId: { type: "string", description: "e.g. solana, bsc, ethereum" },
        pairAddress: { type: "string", description: "Pair address" }
      },
      required: ["chainId", "pairAddress"]
    },
    execute: async ({ chainId, pairAddress }) => {
      const url = `https://api.dexscreener.com/latest/dex/pairs/${chainId}/${pairAddress}`;
      const { data } = await axios.get(url, { timeout: 15000 });
      const p = data?.pairs?.[0];
      if (!p) return { ok: false, error: "Pair not found" };
      return {
        ok: true,
        data: {
          pair: `${p.baseToken?.symbol}/${p.quoteToken?.symbol}`,
          priceUsd: p.priceUsd,
          priceNative: p.priceNative,
          liquidityUsd: p.liquidity?.usd,
          fdv: p.fdv,
          volume24h: p.volume?.h24,
          priceChange: p.priceChange,
          url: p.url
        }
      };
    }
  },
  {
    name: "telegram_alert",
    description:
      "Send a formatted alert to Telegram channel/group using BOT TOKEN and CHAT ID from env.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        message: { type: "string" },
        url: { type: "string" }
      },
      required: ["title", "message"]
    },
    execute: async ({ title, message, url }) => {
      if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
        return { ok: false, error: "Telegram not configured" };
      }
      const text =
        `📢 <b>${title}</b>\n` +
        `${message}${url ? `\n🔗 <a href="${url}">link</a>` : ""}`;
      const tg = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
      await axios.post(
        tg,
        {
          chat_id: TELEGRAM_CHAT_ID,
          text,
          parse_mode: "HTML",
          disable_web_page_preview: true
        },
        { timeout: 15000 }
      );
      return { ok: true };
    }
  }
];

// MCP server mount at /mcp
const mcpServer = new Server(
  { name: "satoshi-signal-mcp", version: "1.0.0", tools },
  { capabilities: { tools: {} } }
);
const transport = new HttpServerTransport({ app, path: "/mcp" });
mcpServer.connect(transport);

app.listen(PORT, () => {
  console.log(`MCP listening on :${PORT}`);
});
