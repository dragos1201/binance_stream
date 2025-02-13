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
@st.cache_data(ttl=300)  # Cache the initial load to reduce database load
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
        .gt("event_time", int(since_timestamp.timestamp() * 1000))  # Convert datetime to ms
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

    # Plot all data with stable Y-Axis range (±20% of median price)
    if prices:
        median_price = pd.Series(prices[-500:]).median()  # Consider last 500 points for median
        y_min = median_price * 0.8  # -20%
        y_max = median_price * 1.2  # +20%

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
            xaxis_tickformat="%H:%M:%S",
            template="plotly_dark",
            height=500,
            yaxis=dict(range=[y_min, y_max]),
            xaxis_rangeslider_visible=True  # Allow zoom and scroll
        )

        chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Control the refresh rate
    time.sleep(1)
