import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client
import datetime

# Supabase credentials (better to set these in Streamlit Secrets for production)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title('Real-Time Binance Trade Dashboard')

# Select coin
selected_coin = st.selectbox('Select Coin Pair', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])

# Initialize session state for data storage
if 'trade_data' not in st.session_state:
    st.session_state['trade_data'] = pd.DataFrame(
        columns=['event_time', 'coin', 'price', 'quantity']
    )
if 'last_fetched_time' not in st.session_state:
    st.session_state['last_fetched_time'] = int(
        (datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=15)).timestamp() * 1000
    )

# Fetch trades from Supabase after a certain timestamp
@st.cache_data(ttl=5)  # Cache for 5 seconds
def fetch_new_trades(since_ms):
    response = (
        supabase.table('trades')
        .select('*')
        .gt('event_time', since_ms)
        .order('event_time')
        .execute()
    )

    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=['event_time', 'coin', 'price', 'quantity'])

# Fetch only new trades
new_data = fetch_new_trades(st.session_state['last_fetched_time'])

if not new_data.empty:
    st.session_state['last_fetched_time'] = new_data['event_time'].max()
    st.session_state['trade_data'] = pd.concat(
        [st.session_state['trade_data'], new_data], ignore_index=True
    )

# Filter data for the selected coin
coin_df = st.session_state['trade_data']
coin_df = coin_df[coin_df['coin'] == selected_coin]

if not coin_df.empty:
    coin_df['event_time'] = pd.to_datetime(coin_df['event_time'], unit='ms')

    st.line_chart(coin_df[['event_time', 'price']].set_index('event_time'))
    st.bar_chart(coin_df[['event_time', 'quantity']].set_index('event_time'))

    st.dataframe(coin_df.tail(10))
else:
    st.warning(f"No trade data available for {selected_coin}")

# Auto-refresh the app every 5 seconds
st.write("Refreshing in 5 seconds...")
st.experimental_sleep(5)
st.rerun()
