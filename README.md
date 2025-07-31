# Satoshi Signal Bot

Satoshi Signal Bot is a Telegram bot that publishes crypto trading signals fetched from DEXScreener.  
Signals are filtered using basic heuristics (volume, liquidity, price change and basic scam checks) and posted to separate Telegram channels for VIP and Public users.

## Features

- **Python 3.11** with `python-telegram-bot` job queue
- Periodic background tasks for VIP (15 min) and public (8h) channels
- Markdown formatted messages with links to DEXScreener
- Basic anti scam heuristics
- Configurable via `.env` and `config.py`

## Usage

1. Install requirements

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with `BOT_TOKEN` (or `TELEGRAM_TOKEN`) and any other credentials.
3. Run the bot

```bash
python bot.py
```

## Testing helpers

`utils_test.py` can be executed to verify API connectivity and message formatting.
