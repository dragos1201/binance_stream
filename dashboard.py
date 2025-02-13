import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
import plotly.graph_objects as go

# Supabase credentials (replace with your actual keys)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Live Crypto Trade Stream")

# Select coin pair
coin_pair = st.selectbox("Select Coin Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

# Container for the plot
chart_placeholder = st.empty()

# Function to fetch latest data from Supabase
def fetch_latest_data():
    response = (
        supabase.table("trades")
        .select("*")
        .eq("coin", coin_pair)
        .order("event_time", desc=True)
        .limit(100)  # Load the last 100 trades
        .execute()
    )
    if response.data:
        df = pd.DataFrame(response.data)
        df["event_time"] = pd.to_datetime(df["event_time"], unit='ms')
        return df.sort_values("event_time")
    return pd.DataFrame(columns=["event_time", "price", "quantity"])

# Live-updating chart loop
prices = []
timestamps = []

while True:
    df = fetch_latest_data()

    if not df.empty:
        prices = df["price"].tolist()
        timestamps = df["event_time"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=prices,
        mode='lines+markers',
        name=coin_pair,
        line=dict(color='royalblue', width=2)
    ))

    fig.update_layout(
        title=f"Live Price Chart - {coin_pair}",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_tickformat="%H:%M:%S",
        template="plotly_dark",
        height=400
    )

    chart_placeholder.plotly_chart(fig, use_container_width=True)

    time.sleep(2)  # Update every 2 seconds
