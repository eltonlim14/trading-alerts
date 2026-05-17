from fastapi import FastAPI, Request
from telegram import Bot
from datetime import datetime
import os

app = FastAPI()

# Get from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
bot = Bot(token=TELEGRAM_TOKEN)

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
            message = f"""
🎯 **RANGE REENTRY ALERT** 🎯

Symbol: {symbol}
Current Price: ${price:.2f}

4-Hour Range:
  📈 High: ${high:.2f}
  📉 Low: ${low:.2f}

✅ Price has re-entered the range!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
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
    """Check current range state"""
    return range_state.get(symbol, {"status": "no data"})

@app.get("/ranges")
async def get_all_ranges():
    """View all tracked ranges"""
    return range_state
