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
    layout="centered",
    initial_sidebar_state="collapsed"
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
    
    /* Reduce top padding on main page */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 700px;
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(10, 13, 20, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
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

st.title("📈 DoubleDown DCA")

# -------------------------------------------------------------------
# SESSION STATE: WATCHLIST WITH CUSTOM THRESHOLDS
# -------------------------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {"ticker": "PLTR", "name": "Palantir Technologies", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "NVDA", "name": "Nvidia", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "TSLA", "name": "Tesla", "dip_threshold": 15.0, "peak_threshold": 20.0},
        {"ticker": "TSM",  "name": "Taiwan Semi", "dip_threshold": 15.0, "peak_threshold": 20.0},
    ]

# -------------------------------------------------------------------
# SIDEBAR: GLASSMORPHISM SETTINGS & WATCHLIST MANAGEMENT
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings & Watchlist")
    
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

# -------------------------------------------------------------------
# DCA RULES ENGINE (CUSTOM THRESHOLDS)
# -------------------------------------------------------------------
def calculate_dca_signal(pct_from_high, dip_thresh, peak_thresh):
    if pct_from_high <= -dip_thresh:
        return "🚀 Double Down", "#3fb950"
    elif pct_from_high >= peak_thresh:
        return "⚠️ Reduce Allocation", "#d29922"
    else:
        return "🟢 Normal DCA", "#58a6ff"

# -------------------------------------------------------------------
# DATA FETCHING & CARDS RENDERING
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
            
            data.append({
                "Ticker": ticker_symbol,
                "Name": item["name"],
                "Price": f"€{current_price:.2f}",
                "52W High": f"€{high_52w:.2f}",
                "Dist. from High": f"{pct_diff:+.1f}%",
                "Action Signal": signal,
                "Color": color
            })
    except Exception:
        data.append({
            "Ticker": ticker_symbol,
            "Name": item["name"],
            "Price": "N/A",
            "52W High": "N/A",
            "Dist. from High": "N/A",
            "Action Signal": "⚠️ Error Fetching",
            "Color": "#f85149"
        })

# Render Sleek Dark Cards
if data:
    for row in data:
        st.markdown(f"""
        <div style="background-color: #0a0d14; border: 1px solid rgba(255,255,255,0.08); padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; font-family: 'Space Grotesk', sans-serif;">
            <div>
                <span style="font-size: 1.2rem; font-weight: bold; color: #ffffff;">{row['Ticker']}</span>
                <span style="color: #8b949e; font-size: 0.9rem; margin-left: 8px;">{row['Name']}</span>
                <div style="color: #8b949e; font-size: 0.85rem; margin-top: 4px;">52W High: {row['52W High']} | Dist: {row['Dist. from High']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; font-weight: bold; color: #ffffff;">{row['Price']}</div>
                <div style="font-size: 0.85rem; font-weight: bold; margin-top: 4px; color: {row['Color']};">{row['Action Signal']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Your watchlist is empty.")

# -------------------------------------------------------------------
# QUICK EXECUTION CHECK & SIMPLIFIED DYNAMIC CHART
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
                
                # Time window selection buttons
                time_window = st.radio(
                    "Time Window", 
                    ["1W", "1M", "3M", "6M", "YTD", "3Y"], 
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                # Filter dataframe based on time window
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
                
                # Calculate average price for selected window
                avg_price = df_filtered['Close'].mean()
                current_window_price = df_filtered['Close'].iloc[-1]
                
                # Switch to green if above window average, red if below
                line_color = "#3fb950" if current_window_price >= avg_price else "#f85149"
                
                df_reset = df_filtered.reset_index()
                date_col = df_reset.columns[0]
                
                fig = px.line(df_reset, x=date_col, y='Close')
                fig.update_layout(
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font_color='#ffffff',
                    font_family='Space Grotesk',
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor='#161b22', zeroline=False),
                    hovermode='x unified'
                )
                fig.update_traces(
                    line=dict(color=line_color, width=2.5),
                    hovertemplate='<b>Price</b>: €%{y:.2f}<br><b>Date</b>: %{x}<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)
