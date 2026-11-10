import streamlit as st
import yfinance as yf
import pandas as pd

# -------------------------------------------------------------------
# APP CONFIG & DARK MODE STYLING
# -------------------------------------------------------------------
st.set_page_config(page_title="Dynamic DCA Strategy Engine", page_icon="📈", layout="centered")

# Custom CSS for Sleek Dark Mode UI matching your reference
st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0b0e14;
        color: #f0f6fc;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #121620;
        color: #f0f6fc;
    }
    
    /* Text & Headers */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #f0f6fc !important;
    }
    
    /* Input Fields & Selectboxes */
    .stTextInput input, .stNumberInput input {
        background-color: #1a202c !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Strategic DCA Action Center")

# -------------------------------------------------------------------
# SESSION STATE: DYNAMIC WATCHLIST
# -------------------------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {"ticker": "PLTR", "name": "Palantir Technologies", "base_pct": 14.3},
        {"ticker": "NVDA", "name": "Nvidia", "base_pct": 7.1},
        {"ticker": "TSLA", "name": "Tesla", "base_pct": 3.6},
        {"ticker": "TSM",  "name": "Taiwan Semi", "base_pct": 7.1},
    ]

# -------------------------------------------------------------------
# SIDEBAR: MANAGE WATCHLIST & BUDGET
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings & Watchlist")
    
    monthly_budget = st.number_input("Total Monthly Budget (€)", min_value=10, value=140, step=10)
    
    st.markdown("---")
    st.subheader("➕ Add Stock")
    with st.form("add_stock_form"):
        new_ticker = st.text_input("Ticker Symbol (e.g. AAPL)").upper().strip()
        new_name = st.text_input("Company Name")
        new_pct = st.number_input("Baseline Weight (%)", min_value=0.5, max_value=100.0, value=5.0, step=0.5)
        submitted = st.form_submit_button("Add to Watchlist")
        
        if submitted and new_ticker:
            if not any(item["ticker"] == new_ticker for item in st.session_state.watchlist):
                st.session_state.watchlist.append({
                    "ticker": new_ticker, 
                    "name": new_name or new_ticker, 
                    "base_pct": new_pct
                })
                st.success(f"Added {new_ticker}!")
                st.rerun()
            else:
                st.warning("Ticker already exists in watchlist.")
                
    st.markdown("---")
    st.subheader("🗑️ Remove Stock")
    tickers_to_remove = [item["ticker"] for item in st.session_state.watchlist]
    selected_to_remove = st.selectbox("Select ticker to remove", tickers_to_remove if tickers_to_remove else ["None"])
    
    if st.button("Remove Selected") and tickers_to_remove:
        st.session_state.watchlist = [item for item in st.session_state.watchlist if item["ticker"] != selected_to_remove]
        st.success(f"Removed {selected_to_remove}!")
        st.rerun()

# -------------------------------------------------------------------
# DCA RULES ENGINE (PERCENTAGE SCALING)
# -------------------------------------------------------------------
def calculate_dca_signal(pct_from_high, base_pct):
    """
    Dynamic Rules Engine:
    - Down >= 15%: Double Down (2x baseline percentage weight)
    - Up >= 20%: Reduce Allocation (0.5x baseline percentage weight)
    - Otherwise: Normal DCA (1.0x baseline percentage weight)
    """
    if pct_from_high <= -15.0:
        return "🚀 Double Down", base_pct * 2.0, "#3fb950"
    elif pct_from_high >= 20.0:
        return "⚠️ Reduce Allocation", base_pct * 0.5, "#d29922"
    else:
        return "🟢 Normal DCA", base_pct * 1.0, "#58a6ff"

# -------------------------------------------------------------------
# DATA FETCHING & DARK CARD DASHBOARD RENDERING
# -------------------------------------------------------------------
st.subheader("Your Dynamic Watchlist & Rules Engine")

data = []
history_cache = {}

for item in st.session_state.watchlist:
    ticker_symbol = item["ticker"]
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            history_cache[ticker_symbol] = hist
            current_price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            pct_diff = ((current_price - high_52w) / high_52w) * 100
            
            signal, target_pct, color = calculate_dca_signal(pct_diff, item["base_pct"])
            suggested_eur = (monthly_budget * target_pct) / 100.0
            
            data.append({
                "Ticker": ticker_symbol,
                "Name": item["name"],
                "Price": f"€{current_price:.2f}",
                "52W High": f"€{high_52w:.2f}",
                "Dist. from High": f"{pct_diff:+.1f}%",
                "Action Signal": signal,
                "Color": color,
                "Target %": f"{target_pct:.1f}%",
                "Suggested €": f"€{suggested_eur:.2f}"
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
            "Target %": f"{item['base_pct']:.1f}%",
            "Suggested €": "N/A"
        })

# Render Sleek Dark Cards (replacing white tables)
if data:
    for row in data:
        st.markdown(f"""
        <div style="background-color: #161b22; border: 1px solid #30363d; padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.2rem; font-weight: bold; color: #ffffff;">{row['Ticker']}</span>
                <span style="color: #8b949e; font-size: 0.9rem; margin-left: 8px;">{row['Name']}</span>
                <div style="color: #8b949e; font-size: 0.85rem; margin-top: 4px;">52W High: {row['52W High']} | Dist: {row['Dist. from High']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; font-weight: bold; color: #ffffff;">{row['Price']}</div>
                <div style="font-size: 0.85rem; font-weight: bold; margin-top: 4px; color: {row['Color']};">{row['Action Signal']}</div>
                <div style="font-size: 0.85rem; color: #8b949e; margin-top: 2px;">Target: {row['Target %']} ({row['Suggested €']})</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Your watchlist is empty. Use the sidebar to add stocks.")

# -------------------------------------------------------------------
# QUICK TRADE EXECUTION CHECK & PRICE CHARTS
# -------------------------------------------------------------------
if st.session_state.watchlist:
    st.markdown("---")
    st.subheader("⚡ Quick Trade Execution Check & Price Chart")
    selected_ticker = st.selectbox("Select stock you are evaluating:", [x["Ticker"] for x in data])
    
    for row in data:
        if row["Ticker"] == selected_ticker:
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Status", row["Action Signal"])
            col2.metric("Target Weight", row["Target %"])
            col3.metric("Suggested Amount", row["Suggested €"], delta=row["Dist. from High"])
            
            # Display 1-Year Stock Price Chart
            if selected_ticker in history_cache:
                st.markdown(f"**{selected_ticker} — 1-Year Price Trend**")
                st.line_chart(history_cache[selected_ticker]['Close'])
