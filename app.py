import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- Professional UI Configuration ---
st.set_page_config(page_title="AlphaTracker | Institutional Scanner", layout="wide", page_icon="🏹")

# Custom CSS for Premium Dark/Modern Trading Dashboard look
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .stDeployButton { display:none; }
    footer { visibility: hidden; }
    .metric-box {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00e676;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏹 AlphaTracker: Live Institutional Block Order Scanner")
st.caption("Tracks smart money algorithms, block trades, and institutional volume spikes on Nifty 50 constituents.")

# --- Verified Nifty 50 Ticker List ---
NIFTY_50_STOCKS = [
    "INFY.NS", "RELIANCE.NS", "BHARTIARTL.NS", "TCS.NS", "HDFCBANK.NS",
    "BAJFINANCE.NS", "ICICIBANK.NS", "HCLTECH.NS", "ADANIENT.NS", "MM.NS", 
    "MARUTI.NS", "SBIN.NS", "TECHM.NS", "ADANIPORTS.NS", "TRENT.NS",
    "KOTAKBANK.NS", "WIPRO.NS", "NTPC.NS", "AXISBANK.NS",
    "TATASTEEL.NS", "HINDALCO.NS", "LT.NS", "JIOFIN.NS", "INDIGO.NS",
    "EICHERMOT.NS", "BEL.NS", "ULTRACEMCO.NS", "TITAN.NS", "ITC.NS",
    "SUNPHARMA.NS", "HINDUNILVR.NS", "POWERGRID.NS", "APOLLOHOSP.NS",
    "COALINDIA.NS", "SHRIRAMFIN.NS", "NESTLEIND.NS", "ASIANPAINT.NS",
    "MAXHEALTH.NS", "CIPLA.NS", "ONGC.NS", "GRASIM.NS", "DRREDDY.NS",
    "HDFCLIFE.NS", "BAJAJFINSV.NS", "JSWSTEEL.NS", "TATACONSUM.NS", "SBILIFE.NS"
]

def convert_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

# --- Core Algorithm Logic ---
def scan_institutional_engine(df, scan_mode):
    triggered_signals = []
    if len(df) < 21:
        return triggered_signals

    # In Live Mode, we only watch the most recent closed candle. In History, we parse the whole day.
    start_idx = len(df) - 1 if scan_mode == "🔴 Live Real-Time Scan" else 20
    end_idx = len(df)

    for i in range(start_idx, end_idx):
        current_candle = df.iloc[i]
        current_volume = current_candle['Volume']
        current_close = current_candle['Close']
        current_time = df.index[i].strftime('%I:%M %p')
        
        # Calculate Dry/Quiet Volume base over preceding 20 periods
        prev_20_candles = df.iloc[i-20:i]
        avg_dry_volume = prev_20_candles['Volume'].mean()
        max_dry_volume = prev_20_candles['Volume'].max()
        
        # Smart Money Entry Condition (Dry consolidation broken by 4.5x average volume explosion)
        if current_volume > (avg_dry_volume * 4.5) and current_volume > max_dry_volume:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_close, 2),
                "Volume": int(current_volume),
                "Avg_Dry_Vol": int(avg_dry_volume),
                "Raw_Index": i
            })
            
    return triggered_signals

# --- JavaScript Alert Injector (Audio + Modal Popup) ---
def trigger_popup_alert(stock_name, price, time_str):
    # Triggers a browser native alert box and plays a notification sound instantly
    popup_html = f"""
    <script>
        var audio = new Audio('https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg');
        audio.play();
        alert('🚨 INSTITUTIONAL ACTIVITY DETECTED!\\n\\nStock: {stock_name}\\nPrice: ₹{price}\\nTime: {time_str}');
    </script>
    """
    st.components.v1.html(popup_html, height=0, width=0)

# --- Sidebar UI Controls ---
st.sidebar.image("https://img.icons8.com/nolan/64/bullish.png", width=50)
st.sidebar.title("AlphaTracker Controls")
selected_mode = st.sidebar.radio("Select Operational Mode:", ["🔴 Live Real-Time Scan", "📅 Last Trading Session History"])
refresh_interval = st.sidebar.slider("Live Auto-Refresh Rate (Seconds):", 15, 60, 30) if selected_mode == "🔴 Live Real-Time Scan" else None
execute_scan = st.sidebar.button("⚡ Start Scanning Engine", type="primary")

# --- Scanning Engine Thread execution ---
if execute_scan or selected_mode == "🔴 Live Real-Time Scan":
    
    # Simple placeholder wrapper for real-time looping
    while True:
        all_signals = []
        stock_counts = {}
        
        if selected_mode == "🔴 Live Real-Time Scan":
            st.toast("🔄 Refreshing Live Engine... Fetching latest ticks.", icon="🚀")
            period_param = "1d"
        else:
            st.info("📊 Fetching historical data pipeline. Please wait...")
            period_param = "5d"

        # Bulk asynchronous-like download to optimize Streamlit cloud speed
        tickers_str = " ".join(NIFTY_50_STOCKS)
        raw_data = yf.download(tickers=tickers_str, period=period_param, interval="1m", group_by='ticker', progress=False)
        
        for ticker in NIFTY_50_STOCKS:
            try:
                if ticker in raw_data.columns.levels[0]:
                    data = raw_data[ticker].dropna()
                else:
                    continue
                    
                if data.empty or len(data) < 25:
                    continue
                    
                data = convert_to_ist(data)
                
                # Filter specifically down to Friday / Last trading day
                all_days = data.index.normalize().unique()
                if len(all_days) >= 1:
                    data = data[data.index.normalize() == all_days[-1]]
                
                signals = scan_institutional_engine(data, selected_mode)
                
                if signals:
                    s_name = ticker.replace(".NS", "")
                    stock_counts[s_name] = len(signals)
                    
                    for sig in signals:
                        all_signals.append({
                            "Stock": s_name,
                            "Time (IST)": sig["Time"],
                            "Execution Price": sig["Price"],
                            "Institutional Volume": sig["Volume"],
                            "Avg Base Vol (20m)": sig["Avg_Dry_Vol"],
                            "Full_Data": data,
                            "Raw_Index": sig["Raw_Index"]
                        })
            except Exception:
                pass
        
        # --- Handle Triggered Results ---
        if all_signals:
            df_signals = pd.DataFrame(all_signals)
            df_signals['Time_Obj'] = pd.to_datetime(df_signals['Time (IST)'], format='%I:%M %p')
            df_signals = df_signals.sort_values(by='Time_Obj', ascending=False) # Latest at the top
            
            # 🚨 TRIGGER POPUP & SOUND FOR LIVE ALERTS
            if selected_mode == "🔴 Live Real-Time Scan":
                latest_alert = df_signals.iloc[0]
                st.balloons() # Visual on-screen celebration
                trigger_popup_alert(latest_alert['Stock'], latest_alert['Execution Price'], latest_alert['Time (IST)'])
                st.error(f"🚨 LIVE ALERT: Institutional block order execution detected in {latest_alert['Stock']} at ₹{latest_alert['Execution Price']}!")
            
            # --- PROFESSIONAL UI BREAKDOWN ---
            col_metrics, col_table = st.columns([1, 3])
            
            with col_metrics:
                st.subheader("💡 Volume Rank")
                df_counts = pd.DataFrame(list(stock_counts.items()), columns=["Stock", "Frequency"]).sort_values(by="Frequency", ascending=False)
                st.dataframe(df_counts, hide_index=True, use_container_width=True)
                
            with col_table:
                st.subheader("📋 Active Signals Terminal")
                df_display = df_signals[["Time (IST)", "Stock", "Execution Price", "Institutional Volume", "Avg Base Vol (20m)"]]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
            # --- GRAPHING GALLERY ---
            st.markdown("---")
            st.subheader("📊 Interactive Execution Visuals")
            for index, row in df_signals.head(5).iterrows():
                with st.expander(f"📈 Chart Studio - {row['Stock']} at {row['Time (IST)']}"):
                    df_chart_all = row['Full_Data']
                    idx = row['Raw_Index']
                    
                    df_slice = df_chart_all.iloc[max(0, idx - 20):min(len(df_chart_all), idx + 15)]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df_slice.index, open=df_slice['Open'], high=df_slice['High'],
                        low=df_slice['Low'], close=df_slice['Close'], name='Price action'
                    ))
                    fig.add_trace(go.Bar(
                        x=df_slice.index, y=df_slice['Volume'], name='Smart Money Volume',
                        yaxis='y2', opacity=0.4, marker_color='#00e676'
                    ))
                    fig.update_layout(
                        template="plotly_dark",
                        yaxis=dict(title='Price (₹)'),
                        yaxis2=dict(title='Volume', overlaying='y', side='right'),
                        xaxis_rangeslider_visible=False,
                        margin=dict(l=20, r=20, t=30, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            break
        else:
            if selected_mode != "🔴 Live Real-Time Scan":
                st.warning("No significant institutional anomalies found matching the current metric constraints.")
                break
                
        # Handle live mode loop delay execution
        if selected_mode == "🔴 Live Real-Time Scan":
            time.sleep(refresh_interval)
            st.rerun()
