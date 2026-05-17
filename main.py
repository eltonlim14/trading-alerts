from fastapi import FastAPI, Request
from datetime import datetime
import os
import requests

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# Simple function to send Telegram message
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

# Store range state for each symbol
range_state = {}

@app.get("/")
async def root():
    return {"status": "online", "message": "Trading Range Alert System"}

@app.post("/webhook")
async def receive_alert(request: Request):
    try:
        body = await request.json()

        symbol = body.get("symbol", "Unknown")
        price = float(body.get("price", 0))
        high = float(body.get("high", 0))
        low = float(body.get("low", 0))

        # Check if price is in range
        in_range = low <= price <= high

        # Get previous state
        prev_state = range_state.get(symbol, {})
        was_outside = prev_state.get("was_outside", False)

        # Update state
        range_state[symbol] = {
            "was_outside": not in_range,
            "price": price,
            "high": high,
            "low": low,
            "timestamp": datetime.now().isoformat()
        }

        # Alert if re-entered range
        alert_sent = False
        if was_outside and in_range:
            message = (
                f"🎯 *RANGE REENTRY ALERT* 🎯\n\n"
                f"Symbol: {symbol}\n"
                f"Current Price: ${price:.2f}\n\n"
                f"4-Hour Range:\n"
                f"  📈 High: ${high:.2f}\n"
                f"  📉 Low: ${low:.2f}\n\n"
                f"✅ Price has re-entered the range!\n\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram(message)
            alert_sent = True

        return {
            "status": "processed",
            "symbol": symbol,
            "in_range": in_range,
            "alert_sent": alert_sent
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500

@app.get("/status/{symbol}")
async def get_status(symbol: str):
    return range_state.get(symbol, {"status": "no data"})

@app.get("/ranges")
async def get_all_ranges():
    return range_state
