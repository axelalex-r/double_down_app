import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# -------------------------------------------------------------------
# APP CONFIG & PURE BLACK / SPACE GROTESK STYLING
# -------------------------------------------------------------------
st.set_page_config(page_title="Dynamic DCA Strategy Engine", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    /* Import Space Grotesk Font */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Apply Font Globally */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* Pure Black App Background */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Dark Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0d14 !important;
        color: #ffffff !important;
    }
    
    /* Text & Headers */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* Input Fields & Selectboxes */
    .stTextInput input, .stNumberInput input {
        background-color: #121824 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #121824 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
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
