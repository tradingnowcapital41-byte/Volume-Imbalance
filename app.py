import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# --- ENTERPRISE THEME & STYLING ARCHITECTURE ---
st.set_page_config(
    page_title="AlphaTerminal | Institutional Block Scanner", 
    layout="wide", 
    page_icon="⚡"
)

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0c0f14 !important;
        color: #d1d4dc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .stDeployButton, footer, header { visibility: hidden !important; }
    .metric-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #787b86;
        margin-bottom: 4px;
    }
    .alert-banner {
        background: rgba(0, 230, 118, 0.1);
        border: 1px solid #00e676;
        padding: 12px;
        border-radius: 4px;
        color: #00e676;
        font-weight: 500;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ AlphaTerminal™")
st.caption("Institutional Order Book Scanner • Target Universe: High-Momentum Dynamic Segments")

# --- TICKER LIST ---
CUSTOM_TICKERS = [
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

def format_to_ist(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

def execute_algorithmic_scan(df, mode_selection):
    signals = []
    if len(df) < 21:
        return signals

    range_start = len(df) - 1 if mode_selection == "REAL-TIME SCALPER ENGINE" else 20
    range_end = len(df)

    for i in range(range_start, range_end):
        candle = df.iloc[i]
        vol = candle['Volume']
        close_p = candle['Close']
        timestamp_str = df.index[i].strftime('%H:%M')
        
        lookback_window = df.iloc[i-20:i]
        base_avg_vol = lookback_window['Volume'].mean()
        base_max_vol = lookback_window['Volume'].max()
        
        if vol > (base_avg_vol * 4.5) and vol > base_max_vol:
            signals.append({
                "Time": timestamp_str,
                "Price": round(close_p, 2),
                "Volume": int(vol),
                "Base_Avg": int(base_avg_vol),
                "Index": i
            })
    return signals

def trigger_terminal_popup(stock_symbol, execution_price, alert_time):
    javascript_payload = f"""
    <script>
        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        var oscillator = audioCtx.createOscillator();
        var gainNode = audioCtx.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        setTimeout(function() {{ oscillator.stop(); }}, 350);
        
        alert('🚨 ALPHA SYSTEM ALERT\\n\\nInstitutional Order Block Captured\\nTicker: {stock_symbol}\\nPrice: INR {execution_price}\\nTimestamp: {alert_time}');
    </script>
    """
    st.components.v1.html(javascript_payload, height=0, width=0)

# --- SIDEBAR INTERFACE ---
st.sidebar.markdown("### TERMINAL ENGINE CONFIG")
selected_engine = st.sidebar.radio(
    "Operational State", 
    ["REAL-TIME SCALPER ENGINE", "HISTORICAL TIMELINE ANALYSIS"]
)
loop_interval = st.sidebar.slider("Dynamic Frame Throttle (Seconds)", 10, 60, 20) if selected_engine == "REAL-TIME SCALPER ENGINE" else None
activation_trigger = st.sidebar.button("INITIALIZE CORE INSTANCES", type="primary", use_container_width=True)

if activation_trigger or selected_engine == "REAL-TIME SCALPER ENGINE":
    
    while True:
        aggregated_signals = []
        rank_distribution = {}
        data_scope = "1d" if selected_engine == "REAL-TIME SCALPER ENGINE" else "7d"
        
        if selected_engine == "REAL-TIME SCALPER ENGINE":
            st.toast("Re-indexing real-time order books...", icon="🔄")
        else:
            st.info("Parsing downstream history arrays in optimized chunks...")

        # ⚡ CHUNKING MECHANISM: Processing 40 stocks at a time to prevent crashes
        chunk_size = 40
        progress_bar = st.progress(0)
        
        for chunk_idx in range(0, len(CUSTOM_TICKERS), chunk_size):
            current_chunk = CUSTOM_TICKERS[chunk_idx : chunk_idx + chunk_size]
            string_payload = " ".join(current_chunk)
            
            # Direct dynamic download
            raw_feed = yf.download(tickers=string_payload, period=data_scope, interval="1m", group_by='ticker', progress=False)
            
            for ticker in current_chunk:
                try:
                    # Clean multi-index data mapping execution
                    if len(current_chunk) == 1:
                        ticker_frame = raw_feed.dropna()
                    elif ticker in raw_feed.columns.levels[0]:
                        ticker_frame = raw_feed[ticker].dropna()
                    else:
                        continue
                        
                    if ticker_frame.empty or len(ticker_frame) < 25:
                        continue
                        
                    ticker_frame = format_to_ist(ticker_frame)
                    
                    calendar_ticks = ticker_frame.index.normalize().unique()
                    if len(calendar_ticks) >= 1:
                        # Extract the exact final active trading session data array
                        ticker_frame = ticker_frame[ticker_frame.index.normalize() == calendar_ticks[-1]]
                    
                    detected_instances = execute_algorithmic_scan(ticker_frame, selected_engine)
                    
                    if detected_instances:
                        clean_symbol = ticker.replace(".NS", "")
                        rank_distribution[clean_symbol] = rank_distribution.get(clean_symbol, 0) + len(detected_instances)
                        
                        for instance in detected_instances:
                            aggregated_signals.append({
                                "Ticker": clean_symbol,
                                "Timestamp (IST)": instance["Time"],
                                "Price (INR)": instance["Price"],
                                "Volume Metric": instance["Volume"],
                                "Historical Base Vol": instance["Base_Avg"],
                                "Context_Data": ticker_frame,
                                "Index_Pos": instance["Index"]
                            })
                except Exception:
                    pass
            
            # Update progress safely
            progress_percent = min((chunk_idx + chunk_size) / len(CUSTOM_TICKERS), 1.0)
            progress_bar.progress(progress_percent)
            
        progress_bar.empty() # Remove progress bar once finished
        
        # --- UI LAYOUT MATRIX RENDERER ---
        if aggregated_signals:
            df_signals = pd.DataFrame(aggregated_signals)
            df_signals['Time_Sort'] = pd.to_datetime(df_signals['Timestamp (IST)'], format='%H:%M')
            df_signals = df_signals.sort_values(by='Time_Sort', ascending=False)
            
            if selected_engine == "REAL-TIME SCALPER ENGINE":
                latest_hit = df_signals.iloc[0]
                trigger_terminal_popup(latest_hit['Ticker'], latest_hit['Price (INR)'], latest_hit['Timestamp (IST)'])
                st.markdown(f"<div class='alert-banner'>⚠️ INSTANT BLOCK TRADING ALERT: Institutional positioning verified on {latest_hit['Ticker']} at Price ₹{latest_hit['Price (INR)']} ({latest_hit['Timestamp (IST)']})</div>", unsafe_allow_html=True)
            
            panel_left, panel_right = st.columns([1, 3])
            
            with panel_left:
                st.markdown("<div class='metric-title'>Volatility Spike Density</div>", unsafe_allow_html=True)
                df_rank = pd.DataFrame(list(rank_distribution.items()), columns=["Asset", "Frequency"]).sort_values(by="Frequency", ascending=False)
                st.dataframe(df_rank, hide_index=True, use_container_width=True)
                
            with panel_right:
                st.markdown("<div class='metric-title'>Live Core Signals Array</div>", unsafe_allow_html=True)
                df_terminal_view = df_signals[["Timestamp (IST)", "Ticker", "Price (INR)", "Volume Metric", "Historical Base Vol"]]
                st.dataframe(df_terminal_view, use_container_width=True, hide_index=True)
                
            st.markdown("### 📊 Array Visualizer Terminal")
            for index, row in df_signals.head(4).iterrows():
                with st.expander(f"📊 Tracking Array Stream: {row['Ticker']} @ {row['Timestamp (IST)']}", expanded=True if index==0 else False):
                    source_matrix = row['Context_Data']
                    target_pos = row['Index_Pos']
                    
                    chart_slice = source_matrix.iloc[max(0, target_pos - 15):min(len(source_matrix), target_pos + 15)]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=chart_slice.index, open=chart_slice['Open'], high=chart_slice['High'],
                        low=chart_slice['Low'], close=chart_slice['Close'], name='Market Price'
                    ))
                    fig.add_trace(go.Bar(
                        x=chart_slice.index, y=chart_slice['Volume'], name='Institutional Tracking Volume',
                        yaxis='y2', opacity=0.35, marker_color='#00e676'
                    ))
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="#131722",
                        plot_bgcolor="#131722",
                        yaxis=dict(title='Price (INR)', gridcolor="#2a2e39"),
                        yaxis2=dict(title='Volume Units', overlaying='y', side='right', showgrid=False),
                        xaxis=dict(gridcolor="#2a2e39"),
                        margin=dict(l=40, r=40, t=10, b=10),
                        xaxis_rangeslider_visible=False,
                        height=320
                    )
                    st.plotly_chart(fig, use_container_width=True)
            break
        else:
            if selected_engine != "REAL-TIME SCALPER ENGINE":
                st.warning("No structural institutional volume spikes matching profile conditions found inside the array footprint.")
                break
                
        if selected_engine == "REAL-TIME SCALPER ENGINE":
            time.sleep(loop_interval)
            st.rerun()
