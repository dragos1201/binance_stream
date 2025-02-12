import streamlit as st
import duckdb
import os
import urllib.request

# GitHub raw URL for DuckDB database (replace YOUR_USERNAME)
GITHUB_DB_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/binance-stream/main/binance_data.db"

# Download database file (if it doesn't exist)
if not os.path.exists("binance_data.db"):
    urllib.request.urlretrieve(GITHUB_DB_URL, "binance_data.db")

# Connect to DuckDB
conn = duckdb.connect("binance_data.db")

st.title("📈 Binance Real-Time Trade Data")

# Fetch latest trades
df = conn.execute("SELECT * FROM trades ORDER BY event_time DESC LIMIT 20").fetchdf()

st.dataframe(df)

# Line chart for price movement
st.line_chart(df.set_index("event_time")["price"])
