import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Volume Breakout Scanner", layout="wide")
st.title("📈 Intraday Volume Breakout Scanner (1-Min TF)")
st.write("Nifty 500 मधील अचानक वॉल्यूम वाढलेले आणि ब्रेकआउट देणारे शेअर्स शोधतो.")

# --- Nifty 500 चे काही प्रातिनिधिक स्टॉक्स (उदाहरणासाठी) ---
# पूर्ण 500 स्टॉक्सची लिस्ट तुम्ही इथे जोडू शकता
NIFTY_500_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "BAJFINANCE.NS",
    "WIPRO.NS", "HCLTECH.NS", "SUNPHARMA.NS", "NTPC.NS", "ADANIENT.NS"
    # इथे तुमचे इतर स्टॉक्स .NS लावून ॲड करा
]

# --- लॉजिक फंक्शन ---
def check_volume_breakout(df):
    if len(df) < 30:  # किमान ३० मिनिटांचा डेटा पाहिजे विश्लेषण करायला
        return False, 0, 0
    
    # शेवटच्या काही कॅंडल्सचा डेटा
    current_volume = df['Volume'].iloc[-1]
    prev_volumes = df['Volume'].iloc[:-1]
    
    # १. चालू मिनिटाचा वॉल्यूम मागच्या २० कॅंडल्सच्या सरासरी (Average) पेक्षा खूप जास्त आहे का? (Expansion)
    avg_volume = prev_volumes.tail(20).mean()
    
    # २. मागच्या ३० कॅंडल्समधील सर्वोच्च वॉल्यूम (Highest Peak) शोधणे
    highest_recent_volume = prev_volumes.tail(30).max()
    
    # ३. लॉजिक: आजच्या दिवसात आधी वॉल्यूम वाढला, मग कमी झाला आणि आता चालू कॅंडलने मागचा हाय तोडला
    if current_volume > (avg_volume * 3) and current_volume > highest_recent_volume:
        return True, current_volume, highest_recent_volume
        
    return False, current_volume, highest_recent_volume

# --- Sidebar UI ---
st.sidebar.header("Settings")
scan_btn = st.sidebar.button("🔍 Scan Nifty 500 Stocks", type="primary")

# --- Scanning Process ---
if scan_btn:
    st.info("स्कॅनिंग सुरू आहे... कृपया थोडा वेळ थांबा (1-Min लाइव्ह डेटा फेच होत आहे)...")
    
    triggered_stocks = []
    
    # प्रोग्रेस बार
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(NIFTY_500_TICKERS):
        try:
            # मागच्या ७ दिवसांचा डेटा (1-min इंटरव्हलसाठी yfinance ला जास्तीत जास्त ७ दिवस मिळतात)
            # आपण फक्त आजचा/ताज्या डेटावर लक्ष केंद्रित करू
            data = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
            
            if data.empty:
                continue
                
            # मल्टि-इंडेक्स कॉलम्स फिक्स करणे (yfinance अपडेटमुळे कधीकधी येते)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                
            is_breakout, curr_vol, max_vol = check_volume_breakout(data)
            
            if is_breakout:
                triggered_stocks.append({
                    "Stock": ticker,
                    "Current Price": round(data['Close'].iloc[-1], 2),
                    "Current Volume": int(curr_vol),
                    "Prev Max Volume": int(max_vol),
                    "Data": data
                })
        except Exception as e:
            pass
        
        # प्रोग्रेस बार अपडेट
        progress_bar.progress((idx + 1) / len(NIFTY_500_TICKERS))
        
    # --- रिझल्ट डिस्प्ले ---
    if triggered_stocks:
        st.success(f"🔥 {len(triggered_stocks)} स्टॉक्स सापडले ज्यांच्यामध्ये वॉल्यूम ब्रेकआउट झाला आहे!")
        
        # टेबल स्वरूपात दाखवणे
        df_display = pd.DataFrame(triggered_stocks)[["Stock", "Current Price", "Current Volume", "Prev Max Volume"]]
        st.dataframe(df_display, use_container_width=True)
        
        # प्रत्येक स्टॉकचा चार्ट दाखवणे
        st.subheader("📊 सविस्तर चार्ट्स")
        for stock in triggered_stocks:
            with st.expander(f"👁️ {stock['Stock']} चा चार्ट पहा"):
                df_chart = stock['Data'].tail(50) # शेवटच्या ५० कॅंडल्स
                
                # Plotly वर कॅंडलस्टिक आणि वॉल्यूम चार्ट
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
                    title=f"{stock['Stock']} - 1 Min Breakout Visual",
                    yaxis=dict(title='Price'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("सध्या कोणत्याही स्टॉकने वॉल्यूम ब्रेकआउटचा क्रायटेरिया मॅच केला नाही. पुन्हा प्रयत्न करा.")
