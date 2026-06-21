import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="Detailed Institutional Scanner", layout="wide")
st.title("🏹 Nifty 50 Full Day Institutional Movement Tracker")
st.write("हा स्कॅनर गेल्या शुक्रवारच्या (Last Trading Session) पूर्ण दिवसात कोणत्या स्टॉकमध्ये कधी-कधी आणि किती वेळा संस्थात्मक हालचाल झाली, त्याची अचूक कुंडली दाखवेल.")

# --- Nifty 50 अचूक स्टॉक लिस्ट ---
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

# --- सुधारित अचूक लॉजिक ---
def scan_all_day_movements(df):
    triggered_signals = []
    if len(df) < 21:
        return triggered_signals

    # सकाळी ९:४५ नंतरच्या सर्व कॅंडल्स तपासू (जेणेकरून सुरुवातीला २० मिनिटांचा बेस मिळेल)
    for i in range(20, len(df)):
        current_candle = df.iloc[i]
        current_volume = current_candle['Volume']
        current_close = current_candle['Close']
        current_time = df.index[i].strftime('%I:%M %p')
        
        # मागच्या २० मिनिटांचा डेटा (कंसोलिडेशन आणि कोरडा वॉल्यूम तपासण्यासाठी)
        prev_20_candles = df.iloc[i-20:i]
        avg_dry_volume = prev_20_candles['Volume'].mean()
        max_dry_volume = prev_20_candles['Volume'].max()
        
        # जर वॉल्यूम सरासरीपेक्षा खूप कमी असेल तर मार्केट शांत आहे.
        # 🎯 अटी: चालू कॅंडलचा वॉल्यूम मागच्या २० मिनिटांच्या सरासरीपेक्षा किमान ४.५ पट पाहिजे 
        # आणि मागच्या २० मिनिटांतील सर्वोच्च वॉल्यूम पीकपेक्षा मोठा पाहिजे!
        if current_volume > (avg_dry_volume * 4.5) and current_volume > max_dry_volume:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_close, 2),
                "Volume": int(current_volume),
                "Avg Dry Vol": int(avg_dry_volume),
                "Raw_Index": i
            })
            
    return triggered_signals

# --- Sidebar UI ---
st.sidebar.header("🕹️ Controls")
scan_btn = st.sidebar.button("⚡ Fetch Friday's Full History", type="primary")

if scan_btn:
    all_signals = []
    stock_counts = {} # कोणता स्टॉक किती वेळा ट्रिगर झाला हे मोजण्यासाठी
    
    st.info("गेल्या शुक्रवारचा पूर्ण दिवसाचा १-मिनिटाचा डेटा गोळा केला जात आहे... कृपया १ मिनिट थांबा...")
    progress_bar = st.progress(0)
    
    # सर्व ५० स्टॉक्स एकाच वेळी डाऊनलोड करू जेणेकरून वेळ वाचेल
    tickers_string = " ".join(NIFTY_50_STOCKS)
    raw_data = yf.download(tickers=tickers_string, period="5d", interval="1m", group_by='ticker', progress=False)
    
    for idx, ticker in enumerate(NIFTY_50_STOCKS):
        try:
            # सिंगल टिकरचा डेटा वेगळा करणे
            if ticker in raw_data.columns.levels[0]:
                data = raw_data[ticker].dropna()
            else:
                continue
                
            if data.empty or len(data) < 30:
                continue
                
            data = convert_to_ist(data)
            
            # फक्त शेवटचा उपलब्ध पूर्ण दिवस (शुक्रवार) फिल्टर करणे
            all_days = data.index.normalize().unique()
            if len(all_days) >= 1:
                last_trading_day = all_days[-1]
                data = data[data.index.normalize() == last_trading_day]
            
            # या शेअरमध्ये दिवसभरात कुठे-कुठे वॉल्यूम स्पाइक आला ते शोधणे
            signals = scan_all_day_movements(data)
            
            if signals:
                stock_name = ticker.replace(".NS", "")
                stock_counts[stock_name] = len(signals) # एकूण किती वेळा ट्रिगर झाला
                
                for sig in signals:
                    all_signals.append({
                        "Stock": stock_name,
                        "Time (IST)": sig["Time"],
                        "Price": sig["Price"],
                        "Institutional Volume": sig["Volume"],
                        "Avg Dry Vol (Previous 20m)": sig["Avg Dry Vol"],
                        "Full_Data": data,
                        "Raw_Index": sig["Raw_Index"]
                    })
        except Exception as e:
            pass
        
        progress_bar.progress((idx + 1) / len(NIFTY_50_STOCKS))
        
    # --- निकाल डिस्प्ले करणे ---
    if all_signals:
        st.success(f"📊 शुक्रवारच्या दिवशी एकूण {len(all_signals)} वेळा संस्थात्मक खरेदीचे मोठे स्पाइक्स दिसले!")
        
        # १. समरी कार्ड्स / काउंटर टेबल
        st.subheader("🎯 कोणत्या शेअरमध्ये किती वेळा 'इन्स्टिट्यूशनल मूव्ह' झाली?")
        df_counts = pd.DataFrame(list(stock_counts.items()), columns=["Stock", "Total Breakouts (Times)"]).sort_values(by="Total Breakouts (Times)", ascending=False)
        
        # कॉलम लेआउट करून समरी दाखवू
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(df_counts, hide_index=True)
            
        with col2:
            st.info("💡 वरच्या टेबलमध्ये ज्या शेअरसमोर जास्त काउंट आहे, त्याचा अर्थ शुक्रवारच्या दिवशी त्या शेअरमध्ये मोठ्या इन्स्टिट्यूशन्सनी (FIIs/DIIs) एकापेक्षा जास्त वेळा मोठ्या ऑर्डर्स टाकून मूव्हमेंट केली होती.")

        st.markdown("---")
        
        # २. संपूर्ण दिवसभराची क्रोनोलॉजिकल लिस्ट (Timeline)
        st.subheader("🕒 शुक्रवारची संपूर्ण टाइमलाईन (वेळेनुसार सर्व शेअर्सची लिस्ट)")
        df_all_signals = pd.DataFrame(all_signals)
        
        # वेळेनुसार सॉर्टिंग (सकाळपासून दुपारी ३:३० पर्यंत)
        df_all_signals['Time_Obj'] = pd.to_datetime(df_all_signals['Time (IST)'], format='%I:%M %p')
        df_all_signals = df_all_signals.sort_values(by='Time_Obj', ascending=True)
        
        df_display = df_all_signals[["Time (IST)", "Stock", "Price", "Institutional Volume", "Avg Dry Vol (Previous 20m)"]]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # ३. विजुअल चार्ट्स गॅलरी
        st.markdown("---")
        st.subheader("📊 टॉप मूव्हमेंट्सचे थेट चार्ट्स तपासा")
        
        # जास्तीत जास्त १५ प्रमुख चार्ट्स दाखवू जेणेकरून ॲप हँग होणार नाही
        for index, row in df_all_signals.head(15).iterrows():
            with st.expander(f"📈 {row['Stock']} - दुपारी/सकाळी {row['Time (IST)']} (Price: {row['Price']})"):
                df_chart_all = row['Full_Data']
                idx = row['Raw_Index']
                
                # ब्रेकआउटच्या मागच्या २० आणि पुढच्या १० कॅंडल्स
                start_c = max(0, idx - 20)
                end_c = min(len(df_chart_all), idx + 15)
                df_slice = df_chart_all.iloc[start_c:end_c]
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df_slice.index, open=df_slice['Open'], high=df_slice['High'],
                    low=df_slice['Low'], close=df_slice['Close'], name='Price'
                ))
                fig.add_trace(go.Bar(
                    x=df_slice.index, y=df_slice['Volume'], name='Volume Spike',
                    yaxis='y2', opacity=0.4, marker_color='green'
                ))
                
                fig.update_layout(
                    title=f"{row['Stock']} Volume Activity at {row['Time (IST)']}",
                    yaxis=dict(title='Price'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
    else:
        st.warning("शुक्रवारच्या डेटामध्ये या क्रायटेरियानुसार एकही सिग्नल सापडला नाही. सिस्टिम पॅरामीटर्स तपासा.")
