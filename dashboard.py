import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client
import datetime
import time

# Supabase credentials (use secrets in production)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch trades from Supabase after a certain timestamp
def fetch_new_trades(since_ms):
    response = (
        supabase.table('trades')
        .select('*')
        .gt('event_time', since_ms)
        .order('event_time', asc=True)
        .execute()
    )
    return pd.DataFrame(response.data)

# Initialize Streamlit App
st.title('Incremental Real-Time Binance Dashboard')

# Select coin
selected_coin = st.selectbox('Select Coin Pair', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])

# Initialize session state for data storage
if 'trade_data' not in st.session_state:
    st.session_state['trade_data'] = pd.DataFrame()
if 'last_fetched_time' not in st.session_state:
    # Start with 15 min ago as initial
    st.session_state['last_fetched_time'] = int((datetime.datetime.utcnow() - datetime.timedelta(minutes=15)).timestamp() * 1000)

# Visualization placeholders
chart_placeholder = st.empty()
bar_placeholder = st.empty()
data_placeholder = st.empty()

while True:
    # Fetch only new trades since last_fetched_time
    new_data = fetch_new_trades(st.session_state['last_fetched_time'])

    if not new_data.empty:
        # Update the last_fetched_time to the latest event_time
        st.session_state['last_fetched_time'] = new_data['event_time'].max()

        # Append new data to session state dataframe
        st.session_state['trade_data'] = pd.concat([st.session_state['trade_data'], new_data], ignore_index=True)

    # Filter by selected coin
    coin_df = st.session_state['trade_data']
    coin_df = coin_df[coin_df['coin'] == selected_coin]

    if not coin_df.empty:
        coin_df['event_time'] = pd.to_datetime(coin_df['event_time'], unit='ms')

        # Plotting
        chart_placeholder.line_chart(coin_df[['event_time', 'price']].set_index('event_time'))
        bar_placeholder.bar_chart(coin_df[['event_time', 'quantity']].set_index('event_time'))

        # Show last few trades
        data_placeholder.dataframe(coin_df.tail(10))

    time.sleep(5)  # Refresh every 5 seconds
