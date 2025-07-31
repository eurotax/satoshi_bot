# Codex Integration Instructions for Satoshi Signal Bot

This document is intended for Codex (https://chat.openai.com/codex) connected to GitHub and Render.

## Project Name: Satoshi Signal Bot

Satoshi Signal Bot is a fully automated Telegram bot that filters and formats high-quality crypto trading signals based on real-time DEX data. It is designed to provide faster, safer, and better-structured signals than the top existing signal groups.

---

## 🔧 Architecture Overview

- Language: Python 3.11+
- Structure: Modular (bot.py, handlers/, filters/, jobs/, scheduler/, scam_checks/, config.py)
- Hosting: Render.com (configured)
- Deployment: GitHub + auto-deploy to Render
- Task queue: asyncio / PTB JobQueue

---

## ✅ Functional Highlights

- Telegram bot using `python-telegram-bot==21.5`
- Fetches and filters new DEX token pairs using DEXScreener API
- Evaluates tokens using fraud filters (renounced ownership, LP lock, taxes, etc.)
- Sends Markdown-rich alerts to:
  - Public Telegram channel (every 8 hours)
  - VIP Telegram channel (every 15 minutes)
- Offers commands: `/start`, `/help`, `/vip`, `/status`, `/signals`
- Environment config in `.env` file
- Two separate PDF documents included for full bot documentation & comparative matrix

---

## 🔍 Codex – Your Task

Codex, you are expected to act as an advanced engineering agent and complete the bot to production-ready state.

### You should:

1. Analyze existing repo structure and documentation
2. Fix any bugs (e.g. unterminated f-string in handlers/commands.py)
3. Ensure all modules are integrated correctly
4. Verify scheduler is correctly posting signals to the appropriate channel with filtering applied
5. Suggest and optionally implement improvements:
   - API fallback/resilience
   - Better formatting
   - Signal queuing/buffering

---

## 🔗 References

- https://github.com/eurotax/satoshi_bot
- https://t.me/SatoshiSignalLab
- https://www.bitget.com/pl/support/articles/12560603798555
- https://kryptopan.pl/crypto-agent-bot-sygnaly-kryptowalutowe/

---

## 📎 Provided Files

- `Satoshi_Signal_Bot_Dokumentacja.pdf`: Full bot description, flow, purpose, and architecture
- `satoshi_bot_vs_top_channels_cleaned.pdf`: Competitive matrix of our bot vs leading signal channels

---

## 🧾 Final Goal

A professional-grade, production-ready crypto signal bot for Telegram, operating reliably 24/7 on Render.com with modular, testable, and maintainable code.

### [!] Important Runtime Notes

- Only one instance of the bot may use polling (`getUpdates`) at a time.
- On Render, always prefer Webhook-based setup to avoid 409 Conflict errors.
- For DEXScreener, avoid using `/dex/pairs/{blockchain}` endpoints directly. Use:
  - `/latest/dex/search?q={token_name}`
  - or `/latest/dex/pairs/{DEX_name}`

### API Tokens

Store your secrets in `.env` file:
```env
TELEGRAM_TOKEN=your_bot_token
DEXSCREENER_API_KEY=not_required_for_public_endpoints
