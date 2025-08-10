import express from "express";
import axios from "axios";

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || "";
const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json());

// Health/keep-alive endpoints
app.get("/", (req, res) => {
  res.status(200).send("Satoshi Bot Server - OK");
});

app.get("/health", (req, res) => {
  res.status(200).json({ 
    ok: true, 
    timestamp: Date.now(),
    service: "satoshi-bot"
  });
});

// Basic API endpoint for testing
app.get("/api/status", (req, res) => {
  res.json({
    status: "running",
    version: "1.0.0",
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, "0.0.0.0", () => {
  console.log(`✅ Satoshi Bot Server running on port ${PORT}`);
  console.log(`🌐 Health check: http://localhost:${PORT}/health`);
});
