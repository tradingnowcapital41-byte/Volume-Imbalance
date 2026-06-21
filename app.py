import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
from concurrent.futures import ThreadPoolExecutor

# --- Professional UI Config (Bloomberg Style) ---
st.set_page_config(page_title="AlphaTracker | Financial Terminal", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0c0f14 !important; color: #d1d4dc !important; }
    .stDeployButton, footer, header { visibility: hidden !important; }
    .alert-banner { background: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; padding: 12px; border-radius: 4px; color: #00e676; font-weight: 500; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("🏹 AlphaTracker™ Terminal")
st.caption("Professional Institutional Scanner for High-Momentum Stocks")

# --- TICKERS POOL ---
TICKERS_POOL = [
    "INFY.NS", "RELIANCE.NS", "BHARTIARTL.NS", "TCS.NS", "HDFCBANK.NS", "NIACL.NS", "IFCI.NS", "TARIL.NS", 
    "AMBER.NS", "BAJFINANCE.NS", "NETWEB.NS", "ICICIBANK.NS", "COFORGE.NS", "HCLTECH.NS", "ADANIENT.NS", 
    "TEJASNET.NS", "ADANIPOWER.NS", "MM.NS", "MARUTI.NS", "HSCL.NS", "SBIN.NS", "BHEL.NS", "ZEEL.NS", 
    "SUZLON.NS", "TECHM.NS", "BSE.NS", "ADANIPORTS.NS", "TRENT.NS", "DATAPATTNS.NS", "BAJAJ-AUTO.NS", 
    "MCX.NS", "PERSISTENT.NS", "KOTAKBANK.NS", "WIPRO.NS", "NTPC.NS", "DIXON.NS", "REDINGTON.NS", 
    "AXISBANK.NS", "TATASTEEL.NS", "IDEA.NS", "OLECTRA.NS", "INDUSINDBK.NS", "HINDALCO.NS", "DMART.NS", 
    "WAAREEENER.NS", "LT.NS", "HFCL.NS", "JIOFIN.NS", "INDIGO.NS", "LICI.NS", "EICHERMOT.NS", "SOLARINDS.NS", 
    "VBL.NS", "POONAWALLA.NS", "BDL.NS", "POLYCAB.NS", "BEL.NS", "ULTRACEMCO.NS", "OLAELEC.NS", "VEDL.NS", 
    "ADANIGREEN.NS", "SAMMAANCAP.NS", "BERGEPAINT.NS", "POWERINDIA.NS", "ABCAPITAL.NS", "CDSL.NS", 
    "JYOTICNC.NS", "TITAN.NS", "NYKAA.NS", "ITC.NS", "SUNPHARMA.NS", "GRSE.NS", "ADANIENSOL.NS", 
    "JBMA.NS", "AUROPHARMA.NS", "CGPOWER.NS", "HAL.NS", "RBLBANK.NS", "SAIL.NS", "BHARATFORG.NS", 
    "BPCL.NS", "MUTHOOTFIN.NS", "YESBANK.NS", "PAGEIND.NS", "KAYNES.NS", "INDUSTOWER.NS", "ANGELONE.NS", 
    "HINDUNILVR.NS", "ZENTEC.NS", "NATIONALUM.NS", "LAURUSLABS.NS", "TORNTPHARM.NS", "TVSMOTOR.NS", 
    "GICRE.NS", "POWERGRID.NS", "JUBLFOOD.NS", "MOTHERSON.NS", "APOLLOHOSP.NS", "ICICIGI.NS", "RADICO.NS", 
    "LUPIN.NS", "COALINDIA.NS", "CARBORUNIV.NS", "UPL.NS", "MPHASIS.NS", "DLF.NS", "SHRIRAMFIN.NS", 
    "NESTLEIND.NS", "GMRAIRPORT.NS", "ATGL.NS", "DIVISLAB.NS", "FEDERALBNK.NS", "NAUKRI.NS", "ASHOKLEY.NS", 
    "CRAFTSMAN.NS", "OFSS.NS", "NBCC.NS", "TATAELXSI.NS", "NLCINDIA.NS", "HINDPETRO.NS", "INDHOTEL.NS", 
    "HEROMOTOCO.NS", "ASIANPAINT.NS", "BATAINDIA.NS", "IOC.NS", "MAXHEALTH.NS", "CANBK.NS", "AWL.NS", 
    "TATACOMM.NS", "CHOLAFIN.NS", "GLENMARK.NS", "JSWENERGY.NS", "CIPLA.NS", "HINDZINC.NS", "UNIONBANK.NS", 
    "KPITTECH.NS", "MAZDOCK.NS", "GAIL.NS", "APARINDS.NS", "NAM-INDIA.NS", "CUMMINSIND.NS", "IDBI.NS", 
    "KEI.NS", "ICICIPRULI.NS", "ONGC.NS", "SCI.NS", "TATAPOWER.NS", "NMDC.NS", "360ONE.NS", "ABB.NS", 
    "COCHINSHIP.NS", "PAYTM.NS", "FORCEMOT.NS", "INOXWIND.NS", "RRKABEL.NS", "GRASIM.NS", "BOSCHLTD.NS", 
    "DRREDDY.NS", "STARHEALTH.NS", "BANDHANBNK.NS", "MARICO.NS", "NAVINFLUOR.NS", "HINDCOPPER.NS", 
    "LODHA.NS", "WOCKPHARMA.NS", "HDFCLIFE.NS", "KALYANKJIL.NS", "BANKINDIA.NS", "JINDALSTEL.NS", 
    "ENGINERSIN.NS", "PFC.NS", "PNB.NS", "FACT.NS", "AUBANK.NS", "BAJAJFINSV.NS", "JSWSTEEL.NS", 
    "TATACONSUM.NS", "COROMANDEL.NS", "KPRMILL.NS", "BRITANNIA.NS", "GODREJCP.NS", "GRANULES.NS", 
    "BANKBARODA.NS", "CARTRADE.NS", "LTF.NS", "PIDILITIND.NS", "RVNL.NS", "IDFCFIRSTB.NS", "VOLTAS.NS", 
    "IRFC.NS", "MAHABANK.NS", "SIEMENS.NS", "INDIANB.NS", "JSWINFRA.NS", "SONACOMS.NS", "PRESTIGE.NS", 
    "SYRMA.NS", "MANKIND.NS", "POLICYBZR.NS", "HDFCAMC.NS", "CGCL.NS", "FORTIS.NS", "SCHAEFFLER.NS", 
    "TATATECH.NS", "PHOENIXLTD.NS", "USHAMART.NS", "GESHIP.NS", "KEC.NS", "RECLTD.NS", "UNITDSPR.NS", 
    "BEML.NS", "KFINTECH.NS", "WELCORP.NS", "CAPLIPOINT.NS", "IIFL.NS", "MANAPPURAM.NS", "CAMS.NS", 
    "OIL.NS", "ZYDUSLIFE.NS", "NHPC.NS", "APLAPOLLO.NS", "AMBUJACEM.NS", "WELSPUNLIV.NS", "NATCOPHARM.NS", 
    "JINDALSAW.NS", "CHENNPETRO.NS", "RPOWER.NS", "MRPL.NS", "CHOICEIN.NS", "SRF.NS", "TIINDIA.NS", 
    "AIAENG.NS", "ANANTRAJ.NS", "ITI.NS", "TITAGARH.NS", "MRF.NS", "BLUESTARCO.NS", "COLPAL.NS", 
    "GODREJPROP.NS", "FIVESTAR.NS", "PATANJALI.NS", "DABUR.NS", "JPPOWER.NS", "HAVELLS.NS", "MOTILALOFS.NS", 
    "DELHIVERY.NS", "CONCOR.NS", "BIOCON.NS", "SONATSOFTW.NS", "AEGISLOG.NS", "EIDPARRY.NS", "PCBL.NS", 
    "GODFRYPHLP.NS", "PPLPHARMA.NS", "PIIND.NS", "ASTRAL.NS", "FLUOROCHEM.NS", "JSL.NS", "JBCHEPHARM.NS", 
    "NUVAMA.NS", "KIRLOSENG.NS", "ASTERDM.NS", "SUPREMEIND.NS", "FINCABLES.NS", "SBILIFE.NS", "GLAND.NS", 
    "PETRONET.NS", "TRITURBINE.NS", "KIMS.NS", "UNOMINDA.NS", "MFSL.NS", "BAJAJHLDNG.NS", "LICHSGFIN.NS", 
    "TIMKEN.NS", "GLAXO.NS", "CENTRALBK.NS", "UBL.NS", "EXIDEIND.NS", "TORNTPOWER.NS", "KARURVYSYA.NS", 
    "DEEPAKFERT.NS", "NEWGEN.NS", "HUDCO.NS", "NCC.NS", "M&MFIN.NS", "SUNDARMFIN.NS", "IREDA.NS", 
    "LEMONTREE.NS", "J&KBANK.NS", "NH.NS", "SBICARD.NS", "ABREL.NS", "MMTC.NS", "ESCORTS.NS", 
    "EMAMILTD.NS", "GMDCLTD.NS", "ZENSARTECH.NS", "ELGIEQUIP.NS", "DEVYANI.NS", "MSUMI.NS", "INTELLECT.NS", 
    "NEULANDLAB.NS", "ALKEM.NS", "CROMPTON.NS", "JKTYRE.NS", "IGL.NS", "IPCALAB.NS", "CHALET.NS", 
    "BLS.NS", "DEEPAKNTR.NS", "LATENTVIEW.NS", "SAREGAMA.NS", "SHYAMMETL.NS", "VTL.NS", "BHARTIHEXA.NS", 
    "FSL.NS", "IRCTC.NS", "DALBHARAT.NS", "CONCORDBIO.NS", "LALPATHLAB.NS", "JMFINANCIL.NS", "ACE.NS", 
    "ZFCVINDIA.NS", "SBFC.NS", "LINDEINDIA.NS", "AFFLE.NS", "PNBHOUSING.NS", "SHREECEM.NS", "BALRAMCHIN.NS", 
    "GRAVITA.NS", "THERMAX.NS", "HONASA.NS", "ECLERX.NS", "BSOFT.NS", "TATAINVEST.NS", "SYNGENE.NS", 
    "CHAMBLFERT.NS", "TATACHEM.NS", "CEATLTD.NS", "AARTIIND.NS", "IEX.NS", "GODREJIND.NS", "RAINBOW.NS", 
    "LTTS.NS", "CYIENT.NS", "GPIL.NS", "APOLLOTYRE.NS", "INDIAMART.NS", "ELECON.NS", "MGL.NS", 
    "BALKRISIND.NS", "NAVA.NS", "CHOLAHLDNG.NS", "BRIGADE.NS", "OBEROIRLTY.NS", "ARE&M.NS", "UCOBANK.NS", 
    "GRAPHITE.NS", "TECHNOE.NS", "IRCON.NS", "SAPPHIRE.NS", "JWL.NS", "CRISIL.NS", "PVRINOX.NS", 
    "CUB.NS", "IRB.NS", "JUBLINGREA.NS", "HONAUT.NS", "TRIDENT.NS", "APTUS.NS", "ACC.NS", "AAVAS.NS", 
    "KAJARIACER.NS", "JKCEMENT.NS", "MINDACORP.NS", "CASTROLIND.NS", "ENDURANCE.NS", "MEDANTA.NS", 
    "RAILTEL.NS", "HOMEFIRST.NS", "SIGNATURE.NS", "ABBOTINDIA.NS", "SJVN.NS", "ABFRL.NS", "HEG.NS", 
    "CCL.NS", "LTFOODS.NS", "UTIAMC.NS", "BAYERCROP.NS", "TEGA.NS", "IOB.NS", "POLYMED.NS", 
    "CREDITACC.NS", "CESC.NS", "MAPMYINDIA.NS", "AJANTPHARM.NS", "ATUL.NS", "SUNTV.NS", "ERIS.NS", 
    "TTML.NS", "SARDAEN.NS", "SWANCORP.NS", "RKFORGE.NS", "BLUEDART.NS", "CIEINDIA.NS", "WHIRLPOOL.NS", 
    "GALLANTT.NS", "RHIM.NS", "CANFINHOME.NS", "ZYDUSWELL.NS", "PFIZER.NS", "EIHOTEL.NS", "3MINDIA.NS", 
    "BIKAJI.NS", "ASAHIINDIA.NS", "CLEAN.NS", "SOBHA.NS", "RITES.NS", "JUBLPHARMA.NS", "INDIACEM.NS", 
    "NUVOCO.NS", "BBTC.NS", "RAMCOCEM.NS", "SUMICHEM.NS", "DCMSHRIRAM.NS"
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
        current_volume = current_candle['Volume']
        current_close = current_candle['Close']
        current_time = df.index[i].strftime('%I:%M %p')
        
        prev_20_candles = df.iloc[i-20:i]
        avg_dry_volume = prev_20_candles['Volume'].mean()
        max_dry_volume = prev_20_candles['Volume'].max()
        
        if current_volume > (avg_dry_volume * 4.5) and current_volume > max_dry_volume:
            triggered_signals.append({
                "Time": current_time,
                "Price": round(current_close, 2),
                "Volume": int(current_volume),
                "Avg Dry Vol": int(avg_dry_volume),
                "Raw_Index": i
            })
    return triggered_signals

# single ticker साठी वेगवान सिम्पल फेचिंग फंक्शन
def fetch_single_ticker_data(ticker, period_param):
    try:
        df = yf.download(tickers=ticker, period=period_param, interval="1m", progress=False)
        if not df.empty and len(df) >= 25:
            return ticker, df
    except Exception:
        pass
    return ticker, None

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

# --- Sidebar Controls ---
st.sidebar.header("🕹️ Control Terminal")
mode = st.sidebar.radio("Select Mode:", ["📅 Last Session History", "🔴 LIVE Market Tracker"])
scan_btn = st.sidebar.button("⚡ Start Terminal Scanner", type="primary", use_container_width=True)

if scan_btn or mode == "🔴 LIVE Market Tracker":
    
    while True:
        all_signals = []
        stock_counts = {}
        
        is_live = (mode == "🔴 LIVE Market Tracker")
        period_param = "1d" if is_live else "5d"
        
        status_msg = st.empty()
        status_msg.info("⚡ Parallel Engine Active: Downloading Nifty 500 stocks concurrently...")

        # ⚡ MULTITHREADING ENGINE (एकाच वेळी २० थ्रेड्स पॅरेलल डेटा खेचतील - सुपरफास्ट)
        downloaded_results = {}
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_single_ticker_data, ticker, period_param) for ticker in TICKERS_POOL]
            for fut in futures:
                t, res_df = fut.result()
                if res_df is not None:
                    downloaded_results[t] = res_df

        status_msg.empty() # प्रोग्रेस मेसेज काढून टाका

        # डाउनलोड झालेल्या डेटावर स्कॅनिंग सुरू
        for ticker, data in downloaded_results.items():
            try:
                data = convert_to_ist(data)
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
            time.sleep(20)
            st.rerun()
