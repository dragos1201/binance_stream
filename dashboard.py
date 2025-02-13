import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
import plotly.graph_objects as go
import os

# ==============================
# Supabase Setup
# ==============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Live Crypto Trade Stream")

# Select coin pair
coin_pair = st.selectbox("Select Coin Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

chart_placeholder = st.empty()

# ==============================
# Step 1 - Load FULL Historical Data Once
# ==============================
@st.cache_data(ttl=300)
def load_full_data(coin):
    response = (
        supabase.table("trades")
        .select("*")
        .eq("coin", coin)
        .order("event_time", desc=False)
        .execute()
    )
    df = pd.DataFrame(response.data)
    if not df.empty:
        df["event_time"] = pd.to_datetime(df["event_time"], unit='ms')
    return df

full_data = load_full_data(coin_pair)

if full_data.empty:
    st.error("No data found for this coin.")
    st.stop()

# Start with all historical data
prices = full_data["price"].tolist()
timestamps = full_data["event_time"].tolist()

# Track the latest event_time for incremental updates
latest_timestamp = full_data["event_time"].iloc[-1]

# ==============================
# Step 2 - Continuously Fetch Only New Data
# ==============================
def fetch_new_data(since_timestamp):
    response = (
        supabase.table("trades")
        .select("*")
        .eq("coin", coin_pair)
        .gt("event_time", int(since_timestamp.timestamp() * 1000))
        .order("event_time", desc=False)
        .execute()
    )

    new_df = pd.DataFrame(response.data)
    if not new_df.empty:
        new_df["event_time"] = pd.to_datetime(new_df["event_time"], unit='ms')
    return new_df

# ==============================
# Step 3 - Live Plotting
# ==============================
while True:
    # Fetch new data since the last timestamp
    new_data = fetch_new_data(latest_timestamp)

    if not new_data.empty:
        # Append new trades
        prices.extend(new_data["price"].tolist())
        timestamps.extend(new_data["event_time"].tolist())

        # Update latest timestamp
        latest_timestamp = new_data["event_time"].iloc[-1]

    # Build Plotly chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=prices,
        mode='lines',
        name=coin_pair,
        line=dict(color='royalblue', width=2)
    ))

    fig.update_layout(
        title=f"Live Price Chart - {coin_pair}",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,  # Enable x-axis scrolling
        template="plotly_dark",
        height=500,
        hovermode="x unified",
    )

    # Allow free zooming on both axes
    fig.update_layout(
        xaxis=dict(fixedrange=False),  # Allow zoom/pan
        yaxis=dict(fixedrange=False)   # Allow zoom/pan
    )

    # Display chart without resetting zoom on every refresh
    chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Control update frequency (2s is a good balance)
    time.sleep(2)
