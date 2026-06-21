import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Institutional Volume Breakout Scanner", layout="wide")
st.title("🏹 Institutional Movement (Smart Money) Scanner")
st.write("लॉजिक: अचानक येणाऱ्या मोठ्या वॉल्यूमच्या संस्थात्मक मूव्हमेंट्स (जसे की image_1746df.png मधील 09:57 AM चा ब्रेकआउट) ट्रॅक करणे.")

# --- तुमच्या स्पेसिफिक NIFTY 50 स्टॉक्सची अचूक लिस्ट ---
NIFTY_50_STOCKS = [
    "INFY.NS", "RELIANCE.NS", "BHARTIARTL.NS", "TCS.NS", "HDFCBANK.NS",
    "BAJFINANCE.NS", "ICICIBANK.NS", "HCLTECH.NS", "ADANIENT.NS", "MM.NS", # M&M चे रूपांतर MM मध्ये केले आहे
    "MARUTI.NS", "SBIN.NS", "TECHM.NS", "ADANIPORTS.NS", "TRENT.NS",
    "KOTAKBANK.NS", "WIPRO.NS", "NTPC.NS", "AXISBANK.NS",
    "TATASTEEL.NS", "HINDALCO.NS", "LT.NS", "JIOFIN.NS", "INDIGO.NS",
    "EICHERMOT.NS", "BEL.NS", "ULTRACEMCO.NS", "TITAN.NS", "ITC.NS",
    "SUNPHARMA.NS", "HINDUNILVR.NS", "POWERGRID.NS", "APOLLOHOSP.NS",
    "COALINDIA.NS", "SHRIRAMFIN.NS", "NESTLEIND.NS", "ASIANPAINT.NS",
    "MAXHEALTH.NS", "CIPLA.NS", "ONGC.NS", "GRASIM.NS", "DRREDDY.NS",
    "HDFCLIFE.NS", "BAJAJFINSV.NS", "JSWSTEEL.NS", "TATACONSUM.NS", "SBILIFE.NS"
    # टीप: ETERNAL, TMPV, BAJAJ-AUTO सारखे सिम्बॉल्स NSE इंडेक्सनुसार व्हेरिफाय करून आवश्यकतेनुसार जोडू शकता
]

def convert_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

# --- कोर इन्स्टिट्यूशनल लॉजिक फंक्शन ---
def scan_institutional_movement(df, is_history_mode=False):
    triggered_signals = []
    if len(df) < 31:
        return triggered_signals

    # सुरुवातीचा बेस तयार होण्यासाठी ३० मिनिटे सोडून पुढे स्कॅन करू
    start_idx = 30 if is_history_mode else len(df) - 1
    end_idx = len(df)

    for i in range(start_idx, end_idx):
        current_candle = df.iloc[i]
        current_close = current_candle['Close']
        current_volume = current_candle['Volume']
        current_time = df.index[i].strftime('%I:%M %p')
        
        # आधीचा संपूर्ण डेटा
        past_data = df.iloc[:i]
        prev_day_high = past_data['High'].max()
        
        # मागच्या २५ कॅंडल्सचा वॉल्यूम (ज्या शांत असायला हव्यात)
        recent_past_volumes = past_data['Volume'].tail(25)
        avg_dry_volume = recent_past_volumes.mean()
        max_dry_volume = recent_past_volumes.max()
        
        # 🎯 इन्स्टिट्यूशनल क्रायटेरिया चेक्स:
        # १. प्राईस ब्रेकआउट: चालू क्लोजिंगने आधीचा डे हाय तोडला पाहिजे किंवा त्याच्या अगदी जवळ पाहिजे.
        is_price_breakout = current_close >= prev_day_high
        
        # २. वॉल्यूम एक्स्पांशन (Spike): चालू मिनिटाचा वॉल्यूम हा मागच्या कोरड्या (Dry) वॉल्यूमच्या सरासरीपेक्षा किमान ५ पट पाहिजे 
        # आणि मागच्या २५ मिनिटांतील कोणत्याही सिंगल वॉल्यूम पीकपेक्षा मोठा पाहिजे.
        is_volume_spike = (current_volume > (avg_dry_volume * 5)) and (current_volume > max_dry_volume)
        
        if is_price_breakout and is_volume_spike:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_close, 2),
                "Old Day High": round(prev_day_high, 2),
                "Institutional Volume": int(current_volume),
                "Avg Dry Volume (25m)": int(avg_dry_volume),
                "Raw_Index": i
            })
            
    return triggered_signals

# --- Sidebar UI ---
st.sidebar.header("🕹️ Scanner Settings")
mode = st.sidebar.radio("मोड निवडा:", ["🔴 Live Scan (Latest 1-Min Candle)", "📅 Friday History (Full Day Scan)"])
scan_btn = st.sidebar.button("⚡ Scan Nifty 50", type="primary")

if scan_btn:
    triggered_stocks = []
    period_param = "1d" if mode == "🔴 Live Scan (Latest 1-Min Candle)" else "5d"
    
    st.info("इन्स्टिट्यूशनल ऑर्डर्सचा शोध घेतला जात आहे... कृपया थांबा...")
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(NIFTY_50_STOCKS):
        try:
            data = yf.download(tickers=ticker, period=period_param, interval="1m", progress=False)
            if data.empty:
                continue
                
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            data = convert_to_ist(data)
            
            # शुक्रवारच्या हिस्ट्रीसाठी फिल्टर
            if mode == "📅 Friday History (Full Day)":
                all_days = data.index.normalize().unique()
                if len(all_days) >= 1:
                    last_trading_day = all_days[-1]
                    data = data[data.index.normalize() == last_trading_day]
            
            signals = scan_institutional_movement(data, is_history_mode=(mode == "📅 Friday History (Full Day)"))
            
            for sig in signals:
                triggered_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Time (IST)": sig["Time"],
                    "Breakout Price": sig["Price"],
                    "Old Day High": sig["Old Day High"],
                    "Big Volume": sig["Institutional Volume"],
                    "Avg Dry Vol": sig["Avg Dry Volume (25m)"],
                    "Full_Data": data,
                    "Raw_Index": sig["Raw_Index"]
                })
        except Exception as e:
            pass
        
        progress_bar.progress((idx + 1) / len(NIFTY_50_STOCKS))
        
    # --- डिस्प्ले रिझल्ट्स ---
    if triggered_stocks:
        df_results = pd.DataFrame(triggered_stocks)
        st.success(f"🔥 {len(df_results)} मोठे संस्थात्मक ब्रेकआउट्स (Smart Money Entries) सापडले!")
        
        df_display = df_results[["Time (IST)", "Stock", "Breakout Price", "Old Day High", "Big Volume", "Avg Dry Vol"]]
        if mode == "📅 Friday History (Full Day)":
            df_display = df_display.sort_values(by="Time (IST)", ascending=False)
            
        st.dataframe(df_display, use_container_width=True)
        
        # विशेष चार्ट व्ह्यू
        st.subheader("📊 इन्स्टिट्यूशनल चार्ट विश्लेषण (जसे तुम्ही image_1746df.png मध्ये पाहिले)")
        for index, stock in df_results.head(10).iterrows():
            with st.expander(f"👁️ {stock['Stock']} - {stock['Time (IST)']} चा बिग वॉल्यूम ब्रेकआउट"):
                df_all = stock['Full_Data']
                idx = stock['Raw_Index']
                
                # मूव्हमेंटच्या आधीच्या आणि नंतरच्या कॅंडल्स दाखवणे
                start_c = max(0, idx - 35)
                end_c = min(len(df_all), idx + 20)
                df_chart = df_all.iloc[start_c:end_c]
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                    low=df_chart['Low'], close=df_chart['Close'], name='Price'
                ))
                fig.add_trace(go.Bar(
                    x=df_chart.index, y=df_chart['Volume'], name='Institutional Volume',
                    yaxis='y2', opacity=0.4, marker_color='rgb(31, 119, 180)'
                ))
                
                fig.add_hline(y=stock['Old Day High'], line_dash="dot", line_color="orange", annotation_text="Prev Swing High")
                
                fig.update_layout(
                    title=f"{stock['Stock']} Big Expansion Target at {stock['Time (IST)']}",
                    yaxis=dict(title='Price'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("या क्षणी कोरड्या वॉल्यूम नंतर अचानक आलेला असा कोणताही मोठा संस्थात्मक ब्रेकआउट सापडला नाही.")
