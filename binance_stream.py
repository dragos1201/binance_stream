import asyncio
import json
import websockets
from supabase import create_client, Client
import os

# Supabase credentials
SUPABASE_URL = "https://kaqrvnymypgcwpggiimk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImthcXJ2bnlteXBnY3dwZ2dpaW1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkzNzg4OTcsImV4cCI6MjA1NDk1NDg5N30.gumJhTdyq6wgIgt2Qu2cm5ArfRbJaUEUyWUZtJZ3Dgk"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Binance WebSocket URL
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@trade"

async def binance_websocket():
    async with websockets.connect(SOCKET) as ws:
        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                # Extract trade data
                trade = {
                    "coin": "BTCUSDT",
                    "event_time": data["T"],
                    "price": float(data["p"]),
                    "quantity": float(data["q"]),
                }

                # Insert into Supabase
                response = supabase.table("trades").insert(trade).execute()
                print("Inserted:", response)

            except Exception as e:
                print("Error:", e)
                break

asyncio.run(binance_websocket())
