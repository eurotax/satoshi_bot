from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Odbierz dane z TradingView
    alert = data.get('alert', '🚨 Alert!')
    symbol = data.get('symbol', 'Unknown Symbol')
    price = data.get('price', 'Unknown Price')
    direction = data.get('direction', 'Unknown Direction')

    message = f"{alert}\n\n🔹Symbol: {symbol}\n🔹Price: {price}\n🔹Direction: {direction}"

    # Wyślij na kanał Telegram
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(telegram_url, json={
        "chat_id": CHANNEL_ID,
        "text": message
    })

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(port=5000)
