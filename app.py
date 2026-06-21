import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# Page Configuration
st.set_page_config(page_title="Volume Breakout Scanner & History", layout="wide")
st.title("📈 Nifty 500 Volume Breakout: Live & Friday History")

# --- Nifty 500 चे काही प्रातिनिधिक स्टॉक्स (इथे पूर्ण ५०० स्टॉक्सची लिस्ट जोडा) ---
NIFTY_500_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "BAJFINANCE.NS",
    "WIPRO.NS", "HCLTECH.NS", "SUNPHARMA.NS", "NTPC.NS", "ADANIENT.NS"
]

# --- भारतीय वेळेनुसार (IST) रूपांतरित करणारे फंक्शन ---
def convert_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

# --- लॉजिक फंक्शन (इतिहास शोधण्यासाठी आणि लाईव्हसाठी) ---
def scan_stock_data(df, is_history_mode=False):
    triggered_signals = []
    if len(df) < 31:
        return triggered_signals

    # जर हिस्ट्री मोड असेल तर पूर्ण दिवसाच्या प्रत्येक कॅंडलवर लूप फिरवून ब्रेकआउट शोधू
    # जर लाईव्ह मोड असेल तर फक्त शेवटच्या (लेटेस्ट) कॅंडलवर लक्ष ठेवू
    start_idx = 30 if is_history_mode else len(df) - 1
    end_idx = len(df)

    for i in range(start_idx, end_idx):
        current_candle = df.iloc[i]
        current_volume = current_candle['Volume']
        current_time = df.index[i].strftime('%I:%M %p') # वेळेचे स्वरूप: 11:30 AM
        
        # मागच्या ३० कॅंडल्सचा डेटा (Rolling window)
        prev_candles = df.iloc[i-30:i]
        prev_volumes = prev_candles['Volume']
        
        avg_volume = prev_volumes.tail(20).mean()
        highest_recent_volume = prev_volumes.max()
        
        # तुमचे लॉजिक: अचानक वॉल्यूम ३ पट पेक्षा जास्त वाढला आणि मागच्या ३० मिनिटांतील सर्वोच्च वॉल्यूम तोडला
        if current_volume > (avg_volume * 3) and current_volume > highest_recent_volume:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_candle['Close'], 2),
                "Volume": int(current_volume),
                "Avg Vol (20)": int(avg_volume),
                "Raw_Index": i # चार्ट बनवण्यासाठी इंडेक्स लक्षात ठेवणे
            })
            
    return triggered_signals

# --- Sidebar UI Settings ---
st.sidebar.header("🕹️ Scanner Controls")
mode = st.sidebar.radio("स्कॅनर मोड निवडा:", ["🔴 Live Scan (Latest Candle)", "📅 Friday History (Full Day)"])
scan_btn = st.sidebar.button("🔍 Start Scanning", type="primary")

# --- मुख्य स्कॅनिंग प्रोसेस ---
if scan_btn:
    triggered_stocks = []
    
    if mode == "🔴 Live Scan (Latest Candle)":
        st.info("चालू लाईव्ह मार्केटचा डेटा स्कॅन होत आहे...")
        period_param = "1d"
    else:
        st.info("गेल्या शुक्रवारचा (Last Trading Session) पूर्ण १-मिनिटाचा डेटा तपासला जात आहे...")
        # शुक्रवारचा डेटा मिळवण्यासाठी '5d' किंवा '2d' कालावधी सुरक्षित राहतो, जेणेकरून वीकेंडलाही डेटा मिळेल
        period_param = "5d" 

    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(NIFTY_500_TICKERS):
        try:
            # 1-Min डेटा फेच करणे
            data = yf.download(tickers=ticker, period=period_param, interval="1m", progress=False)
            
            if data.empty:
                continue
                
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # वेळेला भारतीय वेळेत (IST) सेट करणे
            data = convert_to_ist(data)
            
            # जर हिस्ट्री मोड असेल तर फक्त शेवटच्या उपलब्ध पूर्ण ट्रेडिंग दिवसाचा (उदा. शुक्रवार) डेटा फिल्टर करणे
            if mode == "📅 Friday History (Full Day)":
                all_days = data.index.normalize().unique()
                if len(all_days) >= 1:
                    # शेवटचा उपलब्ध दिवस (जो सामान्यतः शुक्रवार किंवा शेवटचा वर्किंग डे असेल)
                    last_trading_day = all_days[-1] 
                    data = data[data.index.normalize() == last_trading_day]
            
            signals = scan_stock_data(data, is_history_mode=(mode == "📅 Friday History (Full Day)"))
            
            for sig in signals:
                triggered_stocks.append({
                    "Stock": ticker,
                    "Time (IST)": sig["Time"],
                    "Price at Breakout": sig["Price"],
                    "Breakout Volume": sig["Volume"],
                    "Avg Volume": sig["Avg Vol (20)"],
                    "Full_Data": data,
                    "Raw_Index": sig["Raw_Index"]
                })
                
        except Exception as e:
            pass
        
        progress_bar.progress((idx + 1) / len(NIFTY_500_TICKERS))
        
    # --- निकाल दाखवणे ---
    if triggered_stocks:
        df_results = pd.DataFrame(triggered_stocks)
        
        if mode == "📅 Friday History (Full Day)":
            st.success(f"🔥 गेल्या ट्रेडिंग सेशनमध्ये एकूण {len(df_results)} वेळा वॉल्यूम ब्रेकआउट्स झाले होते!")
            # टेबल डिस्प्ले (वेळेनुसार सॉर्ट करून)
            df_display = df_results[["Time (IST)", "Stock", "Price at Breakout", "Breakout Volume", "Avg Volume"]].sort_values(by="Time (IST)", ascending=False)
        else:
            st.success(f"🔥 आत्ताच्या लाईव्ह कॅंडलमध्ये {len(df_results)} शेअर्समध्ये अचानक मोठा वॉल्यूम आला आहे!")
            df_display = df_results[["Stock", "Time (IST)", "Price at Breakout", "Breakout Volume", "Avg Volume"]]
            
        st.dataframe(df_display, use_container_width=True)
        
        # चार्ट्स पाहणे
        st.subheader("📊 सविस्तर चार्ट्स विश्लेषण")
        for index, stock in df_results.head(10).iterrows(): # टॉप १० सिग्नल्सचे चार्ट दाखवू जास्त लोड येऊ नये म्हणून
            with st.expander(f"👁️ {stock['Stock']} - {stock['Time (IST)']} चा चार्ट"):
                df_all = stock['Full_Data']
                idx = stock['Raw_Index']
                
                # ब्रेकआउट वेळेच्या आजूबाजूच्या ३० कॅंडल्स दाखवू
                start_c = max(0, idx - 25)
                end_c = min(len(df_all), idx + 10)
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
                
                fig.update_layout(
                    title=f"{stock['Stock']} Volume Action Around {stock['Time (IST)']}",
                    yaxis=dict(title='Price'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("निवडलेल्या मोडमध्ये कोणताही स्टॉक क्रायटेरिया मॅच करू शकला नाही.")
