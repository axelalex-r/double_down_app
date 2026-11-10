import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# -------------------------------------------------------------------
# APP CONFIG & PURE BLACK / GLASSMORPHISM STYLING
# -------------------------------------------------------------------
st.set_page_config(
    page_title="DoubleDown DCA", 
    page_icon="📈", 
    layout="centered"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* Pure Black App Background */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Top Padding 48px */
    .block-container {
        padding-top: 48px !important;
        padding-bottom: 2rem !important;
        max-width: 700px;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(16, 22, 34, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* Floating Glassmorphism Settings Overlay Modal */
    .settings-overlay {
        position: fixed;
        top: 70px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 500px;
        max-height: 80vh;
        overflow-y: auto;
        background: rgba(10, 13, 20, 0.92);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 24px;
        z-index: 999999;
        box-shadow: 0 20px 40px rgba(0,0,0,0.8);
    }
    
    /* Uniform Pill Radio Buttons */
    .stRadio [role="radiogroup"] {
        display: flex !important;
        gap: 6px !important;
        width: 100% !important;
    }
    .stRadio [role="radiogroup"] label {
        flex: 1 !important;
        text-align: center !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 6px 0 !important;
        margin: 0 !important;
        justify-content: center !important;
        cursor: pointer;
    }
    .stRadio [role="radiogroup"] input[type="radio"] {
        display: none !important;
    }
    .stRadio [role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
    }
    
    /* Text & Headers */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* Input Fields & Selectboxes */
    .stTextInput input, .stNumberInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SESSION STATE: WATCHLIST & SETTINGS TOGGLE
# -------------------------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {"ticker": "PLTR", "name": "Palantir Technologies", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "NVDA", "name": "Nvidia", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "TSLA", "name": "Tesla", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "TSM",  "name": "Taiwan Semi", "dip_threshold": 15.0, "peak_threshold": 20.0},
    ]

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

# -------------------------------------------------------------------
# HEADER & FLOATING SETTINGS OVERLAY
# -------------------------------------------------------------------
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("📈 DoubleDown DCA")
with col_btn:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

if st.session_state.show_settings:
    st.markdown('<div class="settings-overlay">', unsafe_allow_html=True)
    col_head, col_close = st.columns([4, 1])
    with col_head:
        st.subheader("Settings & Watchlist")
    with col_close:
        if st.button("✕", key="close_settings"):
            st.session_state.show_settings = False
            st.rerun()
            
    st.markdown("### ➕ Add Stock")
    with st.form("add_stock_form", clear_on_submit=True):
        new_ticker = st.text_input("Ticker Symbol (e.g. AAPL)").upper().strip()
        new_name = st.text_input("Company Name")
        col_d, col_p = st.columns(2)
        with col_d:
            new_dip = st.number_input("Dip % (-)", min_value=1.0, max_value=50.0, value=15.0, step=1.0)
        with col_p:
            new_peak = st.number_input("Peak % (+)", min_value=1.0, max_value=50.0, value=20.0, step=1.0)
            
        submitted = st.form_submit_button("Add to Watchlist")
        if submitted and new_ticker:
            if not any(item["ticker"] == new_ticker for item in st.session_state.watchlist):
                st.session_state.watchlist.append({
                    "ticker": new_ticker, 
                    "name": new_name or new_ticker, 
                    "dip_threshold": new_dip,
                    "peak_threshold": new_peak
                })
                st.success(f"Added {new_ticker}!")
                st.rerun()
            else:
                st.warning("Ticker already exists.")
                
    st.markdown("---")
    st.subheader("✏️ Edit Thresholds")
    if st.session_state.watchlist:
        edit_ticker = st.selectbox("Select stock to edit", [item["ticker"] for item in st.session_state.watchlist], key="edit_select")
        for item in st.session_state.watchlist:
            if item["ticker"] == edit_ticker:
                with st.form("edit_form"):
                    e_dip = st.number_input("Dip Trigger (%) below 52W High", value=float(item["dip_threshold"]), step=1.0)
                    e_peak = st.number_input("Peak Trigger (%) above 52W High", value=float(item["peak_threshold"]), step=1.0)
                    if st.form_submit_button("Update Thresholds"):
                        item["dip_threshold"] = e_dip
                        item["peak_threshold"] = e_peak
                        st.success(f"Updated {edit_ticker} thresholds!")
                        st.rerun()

    st.markdown("---")
    st.subheader("🗑️ Remove Stock")
    tickers_to_remove = [item["ticker"] for item in st.session_state.watchlist]
    selected_to_remove = st.selectbox("Select ticker to remove", tickers_to_remove if tickers_to_remove else ["None"], key="remove_select")
    if st.button("Remove Selected") and tickers_to_remove:
        st.session_state.watchlist = [item for item in st.session_state.watchlist if item["ticker"] != selected_to_remove]
        st.success(f"Removed {selected_to_remove}!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# DCA RULES ENGINE
# -------------------------------------------------------------------
def calculate_dca_signal(pct_from_high, dip_thresh, peak_thresh):
    if pct_from_high <= -dip_thresh:
        return "🚀 Double Down", "#3fb950"
    elif pct_from_high >= peak_thresh:
        return "⚠️ Reduce Allocation", "#d29922"
    else:
        return "🟢 Normal DCA", "#58a6ff"

# -------------------------------------------------------------------
# DATA FETCHING & CARDS RENDERING WITH SQUARE LOGOS
# -------------------------------------------------------------------
st.subheader("Your Watchlist & DCA Status")

data = []
history_cache = {}

for item in st.session_state.watchlist:
    ticker_symbol = item["ticker"]
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="max")
        
        if not hist.empty:
            history_cache[ticker_symbol] = hist
            current_price = hist['Close'].iloc[-1]
            high_52w = hist['High'].iloc[-252:] if len(hist) >= 252 else hist['High'].max()
            if isinstance(high_52w, pd.Series):
                high_52w = high_52w.max()
            
            pct_diff = ((current_price - high_52w) / high_52w) * 100
            signal, color = calculate_dca_signal(pct_diff, item["dip_threshold"], item["peak_threshold"])
            logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_symbol}"
            
            data.append({
                "Ticker": ticker_symbol,
                "Name": item["name"],
                "Price": f"{current_price:.2f} €",
                "52W High": f"{high_52w:.2f} €",
                "Dist. from High": f"{pct_diff:+.1f}%",
                "Action Signal": signal,
                "Color": color,
                "Logo": logo_url
            })
    except Exception:
        data.append({
            "Ticker": ticker_symbol,
            "Name": item["name"],
            "Price": "N/A",
            "52W High": "N/A",
            "Dist. from High": "N/A",
            "Action Signal": "⚠️ Error Fetching",
            "Color": "#f85149",
            "Logo": ""
        })

if data:
    for row in data:
        st.markdown(f"""
        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="{row['Logo']}" width="36" height="36" style="border-radius: 8px; background: #161b22; object-fit: contain; padding: 2px;" onerror="this.style.display='none'">
                <div>
                    <span style="font-size: 1.2rem; font-weight: bold; color: #ffffff;">{row['Ticker']}</span>
                    <span style="color: #8b949e; font-size: 0.9rem; margin-left: 6px;">{row['Name']}</span>
                    <div style="color: #8b949e; font-size: 0.82rem; margin-top: 2px;">52W High: {row['52W High']} | Dist: {row['Dist. from High']}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; font-weight: bold; color: #ffffff;">{row['Price']}</div>
                <div style="font-size: 0.82rem; font-weight: bold; margin-top: 2px; color: {row['Color']};">{row['Action Signal']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Your watchlist is empty.")

# -------------------------------------------------------------------
# QUICK EXECUTION CHECK & MINIMALIST CHART
# -------------------------------------------------------------------
if st.session_state.watchlist:
    st.markdown("---")
    st.subheader("⚡ Quick Trade Execution Check & Chart")
    selected_ticker = st.selectbox("Select stock to analyze:", [x["Ticker"] for x in data], key="chart_select")
    
    for row in data:
        if row["Ticker"] == selected_ticker:
            st.metric("Current Status", row["Action Signal"], delta=row["Dist. from High"])
            
            if selected_ticker in history_cache:
                full_hist = history_cache[selected_ticker]
                
                time_window = st.radio(
                    "Time Window", 
                    ["1W", "1M", "3M", "6M", "YTD", "3Y"], 
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                now = full_hist.index[-1]
                if time_window == "1W":
                    start_date = now - timedelta(days=7)
                elif time_window == "1M":
                    start_date = now - timedelta(days=30)
                elif time_window == "3M":
                    start_date = now - timedelta(days=90)
                elif time_window == "6M":
                    start_date = now - timedelta(days=180)
                elif time_window == "YTD":
                    start_date = pd.Timestamp(now.year, 1, 1, tz=now.tz) if now.tz else pd.Timestamp(now.year, 1, 1)
                elif time_window == "3Y":
                    start_date = now - timedelta(days=365*3)
                else:
                    start_date = full_hist.index[0]
                    
                df_filtered = full_hist[full_hist.index >= start_date].copy()
                if df_filtered.empty:
                    df_filtered = full_hist.tail(10)
                
                avg_price = df_filtered['Close'].mean()
                current_window_price = df_filtered['Close'].iloc[-1]
                
                line_color = "#3fb950" if current_window_price >= avg_price else "#f85149"
                
                df_reset = df_filtered.reset_index()
                date_col = df_reset.columns[0]
                
                fig = px.line(df_reset, x=date_col, y='Close')
                
                # Minimalist chart layout filling box entirely with no axes/numbers/grid
                fig.update_layout(
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font_color='#ffffff',
                    font_family='Space Grotesk',
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False),
                    hovermode='x unified',
                    dragmode=False,
                    hoverlabel=dict(
                        bgcolor='rgba(16, 22, 34, 0.95)',
                        bordercolor='rgba(255, 255, 255, 0.2)',
                        font=dict(family='Space Grotesk', color='#ffffff', size=13)
                    )
                )
                
                # Clean hover format: Date on first line, price on second line
                fig.update_traces(
                    line=dict(color=line_color, width=2.5),
                    hovertemplate='<b>%{x|%b %d, %Y}</b><br>%{y:.2f} €<extra></extra>'
                )
                
                st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    config={
                        'displayModeBar': False,
                        'scrollZoom': False,
                        'doubleClick': False
                    }
                )
                
