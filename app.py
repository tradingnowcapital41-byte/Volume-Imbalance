import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Day High Volume Breakout Scanner", layout="wide")
st.title("🚀 Day High + Volume Breakout Scanner (1-Min TF)")
st.write("लॉजिक: आधी वॉल्यूमसह Day High बनणार -> मग शांत होणार -> पुन्हा तो Day High मोठ्या वॉल्यूमने ब्रेक होणार!")

# --- Nifty 500 चे काही प्रातिनिधिक स्टॉक्स ---
NIFTY_500_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "BAJFINANCE.NS",
    "WIPRO.NS", "HCLTECH.NS", "SUNPHARMA.NS", "NTPC.NS", "ADANIENT.NS"
]

def convert_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

# --- कोर लॉजिक फंक्शन ---
def scan_day_high_breakout(df, is_history_mode=False):
    triggered_signals = []
    if len(df) < 31:
        return triggered_signals

    # सुरवातीला किमान ३० मिनिटांचा डेटा सोडून पुढे तपासू जेणेकरून एक बेस Day High तयार झालेला असेल
    start_idx = 30 if is_history_mode else len(df) - 1
    end_idx = len(df)

    for i in range(start_idx, end_idx):
        current_candle = df.iloc[i]
        current_close = current_candle['Close']
        current_volume = current_candle['Volume']
        current_time = df.index[i].strftime('%I:%M %p')
        
        # १. चालू कॅंडलच्या आधीचा संपूर्ण दिवसाचा डेटा (इथून आपण आधीचा Day High आणि Max Volume काढणार)
        past_day_data = df.iloc[:i]
        
        prev_day_high = past_day_data['High'].max()
        prev_max_volume = past_day_data['Volume'].max()
        avg_volume_20 = past_day_data['Volume'].tail(20).mean()
        
        # २. लॉजिक चेक्स:
        # क) चालू क्लोजिंगने मागचा Day High तोडला पाहिजे (Day High Breakout)
        is_price_breakout = current_close > prev_day_high
        
        # ख) चालू वॉल्यूम हा मागच्या सर्वोच्च वॉल्यूपेक्षा जास्त पाहिजे आणि सरासरीपेक्षा किमान ३ पट पाहिजे
        is_volume_breakout = (current_volume > prev_max_volume) and (current_volume > (avg_volume_20 * 3))
        
        if is_price_breakout and is_volume_breakout:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_close, 2),
                "Prev Day High": round(prev_day_high, 2),
                "Breakout Volume": int(current_volume),
                "Prev Max Volume": int(prev_max_volume),
                "Raw_Index": i
            })
            
    return triggered_signals

# --- Sidebar UI ---
st.sidebar.header("🕹️ Controls")
mode = st.sidebar.radio("स्कॅनर मोड निवडा:", ["🔴 Live Scan (Latest Candle)", "📅 Friday History (Full Day)"])
scan_btn = st.sidebar.button("🔍 Start Scanning", type="primary")

if scan_btn:
    triggered_stocks = []
    period_param = "1d" if mode == "🔴 Live Scan (Latest Candle)" else "5d"
    
    st.info("डेटा फेच आणि फिल्टर होत आहे... कृपया थांबा...")
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(NIFTY_500_TICKERS):
        try:
            data = yf.download(tickers=ticker, period=period_param, interval="1m", progress=False)
            if data.empty:
                continue
                
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            data = convert_to_ist(data)
            
            # शुक्रवार/लास्ट ट्रेडिंग सेशनसाठी फिल्टर
            if mode == "📅 Friday History (Full Day)":
                all_days = data.index.normalize().unique()
                if len(all_days) >= 1:
                    last_trading_day = all_days[-1]
                    data = data[data.index.normalize() == last_trading_day]
            
            signals = scan_day_high_breakout(data, is_history_mode=(mode == "📅 Friday History (Full Day)"))
            
            for sig in signals:
                triggered_stocks.append({
                    "Stock": ticker,
                    "Time (IST)": sig["Time"],
                    "Breakout Price": sig["Price"],
                    "Old Day High": sig["Prev Day High"],
                    "New Volume": sig["Breakout Volume"],
                    "Old Max Volume": sig["Prev Max Volume"],
                    "Full_Data": data,
                    "Raw_Index": sig["Raw_Index"]
                })
        except Exception as e:
            pass
        
        progress_bar.progress((idx + 1) / len(NIFTY_500_TICKERS))
        
    # --- डिस्प्ले रिझल्ट्स ---
    if triggered_stocks:
        df_results = pd.DataFrame(triggered_stocks)
        st.success(f"🔥 तुमच्या 'Day High + Volume Breakout' लॉजिकनुसार {len(df_results)} सिग्नल्स सापडले!")
        
        df_display = df_results[["Time (IST)", "Stock", "Breakout Price", "Old Day High", "New Volume", "Old Max Volume"]]
        if mode == "📅 Friday History (Full Day)":
            df_display = df_display.sort_values(by="Time (IST)", ascending=False)
            
        st.dataframe(df_display, use_container_width=True)
        
        # चार्ट विजुअलायझेशन
        st.subheader("📊 सिग्नल्सचे चार्ट्स (Zoomed View)")
        for index, stock in df_results.head(10).iterrows():
            with st.expander(f"👁️ {stock['Stock']} - {stock['Time (IST)']} चा ब्रेकआउट पहा"):
                df_all = stock['Full_Data']
                idx = stock['Raw_Index']
                
                start_c = max(0, idx - 30)
                end_c = min(len(df_all), idx + 15)
                df_chart = df_all.iloc[start_c:end_c]
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                    low=df_chart['Low'], close=df_chart['Close'], name='Price'
                ))
                fig.add_trace(go.Bar(
                    x=df_chart.index, y=df_chart['Volume'], name='Volume',
                    yaxis='y2', opacity=0.3
                ))
                
                # जुना डे हाय दाखवण्यासाठी एक हॉरिझॉन्टल लाईन
                fig.add_hline(y=stock['Old Day High'], line_dash="dash", line_color="red", annotation_text="Old Day High")
                
                fig.update_layout(
                    title=f"{stock['Stock']} - Breakout at {stock['Time (IST)']}",
                    yaxis=dict(title='Price'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("या क्रायटेरियामध्ये बसणारा कोणताही स्टॉक सध्या सापडला नाही.")
