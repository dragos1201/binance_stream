import asyncio
import websockets
import json
import duckdb
import os
from datetime import datetime
import subprocess

# Database file (stored in repo)
DB_FILE = "binance_data.db"

# Connect to DuckDB
conn = duckdb.connect(DB_FILE)

# Create table if it doesn't exist
conn.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        coin STRING,
        event_time TIMESTAMP,
        price FLOAT,
        quantity FLOAT
    )
""")

async def fetch_binance_trades():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    
    async with websockets.connect(url) as ws:
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            trade = (
                "BTCUSDT",
                datetime.utcfromtimestamp(data["T"] / 1000),  # Convert ms to timestamp
                float(data["p"]),
                float(data["q"])
            )
            
            # Insert into DuckDB
            conn.execute("INSERT INTO trades VALUES (?, ?, ?, ?)", trade)
            conn.commit()  # Save data
            
            # Commit updated database to GitHub
            commit_to_github()

def commit_to_github():
    """Commits and pushes the updated DuckDB file to the repository."""
    os.system("git config --global user.name 'github-actions'")
    os.system("git config --global user.email 'actions@github.com'")
    os.system("git add binance_data.db")
    os.system("git commit -m 'Update trade data'")
    os.system("git push")

asyncio.run(fetch_binance_trades())
