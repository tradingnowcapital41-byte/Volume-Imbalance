import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- Terminal Professional UI Config ---
st.set_page_config(page_title="AlphaTracker | Financial Terminal", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0c0f14 !important; color: #d1d4dc !important; }
    .stDeployButton, footer, header { visibility: hidden !important; }
    .alert-banner { background: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; padding: 12px; border-radius: 4px; color: #00e676; font-weight: 500; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("🏹 AlphaTracker™ Terminal")
st.caption("Institutional Volume Scanner • High-Momentum Mid & SmallCap Universe (Non-F&O)")

# --- ⚡ NEW 100 HIGH-VOLUME MID/SMALLCAP STOCKS POOL (F&O सोडून कडक मोमेंटम वाले) ---
TICKERS_POOL = [
    "NIACL.NS", "TARIL.NS", "AMBER.NS", "NETWEB.NS", "TEJASNET.NS", "HSCL.NS", "DATAPATTNS.NS", 
    "OLECTRA.NS", "WAAREEENER.NS", "HFCL.NS", "SOLARINDS.NS", "POONAWALLA.NS", "BDL.NS", "OLAELEC.NS", 
    "POWERINDIA.NS", "JYOTICNC.NS", "GRSE.NS", "JBMA.NS", "CGPOWER.NS", "KAYNES.NS", "ZENTEC.NS", 
    "LAURUSLABS.NS", "GICRE.NS", "RADICO.NS", "CARBORUNIV.NS", "GMRAIRPORT.NS", "CRAFTSMAN.NS", 
    "NBCC.NS", "NLCINDIA.NS", "INDHOTEL.NS", "AWL.NS", "TATACOMM.NS", "GLENMARK.NS", "JSWENERGY.NS", 
    "MAZDOCK.NS", "APARINDS.NS", "NAM-INDIA.NS", "CUMMINSIND.NS", "KEI.NS", "SCI.NS", "COCHINSHIP.NS", 
    "FORCEMOT.NS", "INOXWIND.NS", "RRKABEL.NS", "STARHEALTH.NS", "WOCKPHARMA.NS", "KALYANKJIL.NS", 
    "ENGINERSIN.NS", "FACT.NS", "COROMANDEL.NS", "KPRMILL.NS", "GRANULES.NS", "CARTRADE.NS", "LTF.NS", 
    "IDFCFIRSTB.NS", "JSWINFRA.NS", "SONACOMS.NS", "PRESTIGE.NS", "SYRMA.NS", "MANKIND.NS", "POLICYBZR.NS", 
    "CGCL.NS", "FORTIS.NS", "SCHAEFFLER.NS", "TATATECH.NS", "PHOENIXLTD.NS", "USHAMART.NS", "GESHIP.NS", 
    "KEC.NS", "BEML.NS", "KFINTECH.NS", "WELCORP.NS", "CAPLIPOINT.NS", "IIFL.NS", "MANAPPURAM.NS", 
    "CAMS.NS", "WELSPUNLIV.NS", "NATCOPHARM.NS", "JINDALSAW.NS", "CHENNPETRO.NS", "RPOWER.NS", "MRPL.NS", 
    "CHOICEIN.NS", "ANANTRAJ.NS", "ITI.NS", "TITAGARH.NS", "BLUESTARCO.NS", "FIVESTAR.NS", "PATANJALI.NS", 
    "JPPOWER.NS", "MOTILALOFS.NS", "DELHIVERY.NS", "SONATSOFTW.NS", "AEGISLOG.NS", "EIDPARRY.NS", 
    "PCBL.NS", "GODFRYPHLP.NS", "PPLPHARMA.NS", "FLUOROCHEM.NS", "JBCHEPHARM.NS"
]

def convert_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

def scan_all_day_movements(df, live_mode=False):
    triggered_signals = []
    if len(df) < 21:
        return triggered_signals

    start_idx = len(df) - 1 if live_mode else 20
    for i in range(start_idx, len(df)):
        current_candle = df.iloc[i]
        vol = current_candle['Volume']
        close_p = current_candle['Close']
        time_str = df.index[i].strftime('%I:%M %p')
        
        prev_20 = df.iloc[i-20:i]
        avg_vol = prev_20['Volume'].mean()
        max_vol = prev_20['Volume'].max()
        
        if vol > (avg_vol * 4.5) and vol > max_vol:
            triggered_signals.append({
                "Time": time_str,
                "Price": round(close_p, 2),
                "Volume": int(vol),
                "Avg Dry Vol": int(avg_vol),
                "Raw_Index": i
            })
    return triggered_signals

def trigger_popup_alert(stock_name, price, time_str):
    popup_html = f"""
    <script>
        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        var oscillator = audioCtx.createOscillator();
        var gainNode = audioCtx.createGain();
        oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
        oscillator.connect(gainNode); gainNode.connect(audioCtx.destination);
        oscillator.start(); setTimeout(function() {{ oscillator.stop(); }}, 350);
        alert('🚨 INSTITUTIONAL SIGNAL\\n\\nStock: {stock_name}\\nPrice: ₹{price}\\nTime: {time_str}');
    </script>
    """
    st.components.v1.html(popup_html, height=0, width=0)

# --- Sidebar UI ---
st.sidebar.header("🕹️ Control Terminal")
mode = st.sidebar.radio("Select Mode:", ["📅 Last Session History", "🔴 LIVE Market Tracker"])
scan_btn = st.sidebar.button("⚡ Start Terminal Scanner", type="primary", use_container_width=True)

if scan_btn or mode == "🔴 LIVE Market Tracker":
    
    while True:
        all_signals = []
        stock_counts = {}
        is_live = (mode == "🔴 LIVE Market Tracker")
        period_param = "1d" if is_live else "5d"
        
        status = st.empty()
        status.info("⏳ Processing Core High-Volume Stream... (Taking 5-7 Seconds)")

        # ⚡ Secure Batch Download (नो-ब्लॉक, १०० स्टॉक्स एकदम सेफ आणि सुपरफास्ट)
        tickers_string = " ".join(TICKERS_POOL)
        raw_data = yf.download(tickers=tickers_string, period=period_param, interval="1m", group_by='ticker', progress=False)
        
        status.empty()

        for ticker in TICKERS_POOL:
            try:
                if ticker in raw_data.columns.levels[0]:
                    data = raw_data[ticker].dropna()
                else:
                    continue
                if data.empty or len(data) < 25:
                    continue
                    
                data = convert_to_ist(data)
                
                # शेवटचा ट्रेडिंग दिवस फिल्टर करणे
                all_days = data.index.normalize().unique()
                if len(all_days) >= 1:
                    data = data[data.index.normalize() == all_days[-1]]
                
                signals = scan_all_day_movements(data, live_mode=is_live)
                
                if signals:
                    stock_name = ticker.replace(".NS", "")
                    stock_counts[stock_name] = stock_counts.get(stock_name, 0) + len(signals)
                    
                    for sig in signals:
                        all_signals.append({
                            "Stock": stock_name,
                            "Time (IST)": sig["Time"],
                            "Price": sig["Price"],
                            "Volume": sig["Volume"],
                            "Avg Dry Vol": sig["Avg Dry Vol"],
                            "Full_Data": data,
                            "Raw_Index": sig["Raw_Index"]
                        })
            except Exception:
                pass
        
        # --- डिस्प्ले रिझल्ट्स ---
        if all_signals:
            df_signals = pd.DataFrame(all_signals)
            df_signals['Time_Obj'] = pd.to_datetime(df_signals['Time (IST)'], format='%I:%M %p')
            df_signals = df_signals.sort_values(by='Time_Obj', ascending=False)
            
            if is_live:
                latest = df_signals.iloc[0]
                trigger_popup_alert(latest['Stock'], latest['Price'], latest['Time (IST)'])
                st.markdown(f"<div class='alert-banner'>🚨 LIVE INSTANT SIGNAL: Smart money activity detected in <b>{latest['Stock']}</b> at ₹{latest['Price']} ({latest['Time (IST)']})</div>", unsafe_allow_html=True)

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Density Rank")
                df_counts = pd.DataFrame(list(stock_counts.items()), columns=["Stock", "Signals"]).sort_values(by="Signals", ascending=False)
                st.dataframe(df_counts, hide_index=True, use_container_width=True)
                
            with col2:
                st.markdown("### 📋 Core Signals Grid")
                df_display = df_signals[["Time (IST)", "Stock", "Price", "Volume", "Avg Dry Vol"]]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
            st.markdown("---")
            st.subheader("📊 Chart Analysis Terminal")
            for index, row in df_signals.head(4).iterrows():
                with st.expander(f"📈 {row['Stock']} - {row['Time (IST)']} (Price: {row['Price']})", expanded=True if index==0 else False):
                    df_slice = row['Full_Data'].iloc[max(0, row['Raw_Index'] - 15):min(len(row['Full_Data']), row['Raw_Index'] + 15)]
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=df_slice.index, open=df_slice['Open'], high=df_slice['High'], low=df_slice['Low'], close=df_slice['Close'], name='Price'))
                    fig.add_trace(go.Bar(x=df_slice.index, y=df_slice['Volume'], name='Volume Spike', yaxis='y2', opacity=0.35, marker_color='#00e676'))
                    fig.update_layout(template="plotly_dark", yaxis=dict(title='Price'), yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False), xaxis_rangeslider_visible=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
            break
        else:
            if not is_live:
                st.warning("No dynamic institutional breakouts found in this session.")
                break
                
        if is_live:
            time.sleep(25)
            st.rerun()
