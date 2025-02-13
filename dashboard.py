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
# Step 3 - User Control for Auto-Scrolling / Free Mode
# ==============================
live_mode = st.toggle("Live Mode (Scroll with Data)", value=True)

# Allow user to pick "last N minutes" window for convenience
window_minutes = st.slider("Show Last N Minutes", 1, 60, 10)

# ==============================
# Step 4 - Live Plotting
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

    # Plotting
    fig.update_layout(
        title=f"Live Price Chart - {coin_pair}",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark",
        height=500,
        hovermode="x unified",
        xaxis_rangeslider_visible=True,
    )

    # Adjust Y-axis for zooming
    fig.update_yaxes(fixedrange=False)

    # Manage X-axis live view or custom view
    if live_mode:
        # Show only the last N minutes in the main chart view
        end_time = timestamps[-1]
        start_time = end_time - pd.to_timedelta(window_minutes, unit='m')
        fig.update_xaxes(range=[start_time, end_time])
    else:
        # Free zoom/pan mode – do nothing; user controls it
        fig.update_xaxes(fixedrange=False)

    # Show the plot
    chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Slow down the loop to avoid rate limits / freezing
    time.sleep(2)
