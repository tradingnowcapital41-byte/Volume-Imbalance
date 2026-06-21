import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="AlphaTracker | Terminal", layout="wide")

# UI Styling
st.markdown("""
<style>
    .stApp { background-color: #0c0f14; color: #d1d4dc; }
    .alert-banner { background: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; padding: 10px; border-radius: 5px; color: #00e676; }
</style>
""", unsafe_allow_html=True)

st.title("🏹 AlphaTracker™ Terminal")

# २५ हाय-मोमेंटम स्टॉक्स (जास्त स्टॉक्स = क्रॅशचा धोका, म्हणून २५ ठेवलेत)
TICKERS_POOL = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "MAZDOCK.NS", "COCHINSHIP.NS", "SUZLON.NS", "ZOMATO.NS", "IRFC.NS",
    "RVNL.NS", "TATATECH.NS", "OLECTRA.NS", "WAAREEENER.NS", "HFCL.NS",
    "KPITTECH.NS", "BEL.NS", "HAL.NS", "KEI.NS", "NBCC.NS",
    "CDSL.NS", "BSE.NS", "MCX.NS", "ANGELONE.NS", "CAMS.NS"
]

@st.cache_data(ttl=60)
def get_data(tickers):
    return yf.download(tickers=tickers, period="1d", interval="1m", group_by='ticker', progress=False)

mode = st.sidebar.radio("Mode:", ["History", "Live Tracker"])
if st.sidebar.button("⚡ Run Scanner"):
    data = get_data(" ".join(TICKERS_POOL))
    
    if data is not None and not data.empty:
        signals_found = False
        for ticker in TICKERS_POOL:
            try:
                df = data[ticker].dropna()
                if len(df) < 20: continue
                
                # Volume Spike Logic
                avg_vol = df['Volume'].rolling(20).mean()
                if df['Volume'].iloc[-1] > (avg_vol.iloc[-1] * 3):
                    signals_found = True
                    st.markdown(f"<div class='alert-banner'>🚨 {ticker} - Volume Spike! Price: ₹{df['Close'].iloc[-1]:.2f}</div>", unsafe_allow_html=True)
            except: continue
        
        if not signals_found:
            st.warning("No spikes found yet.")
    else:
        st.error("Data fetch failed. Wait for 10 seconds and try again.")

    if mode == "Live Tracker":
        time.sleep(30)
        st.rerun()
