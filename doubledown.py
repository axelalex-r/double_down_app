import streamlit as st
import yfinance as yf
import pandas as pd

# -------------------------------------------------------------------
# APP CONFIG & TITLE
# -------------------------------------------------------------------
st.set_page_config(page_title="Dynamic DCA Strategy Engine", page_icon="📈", layout="centered")
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
    
    # Monthly budget input for scaling percentages to currency
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
        return "🚀 Double Down", base_pct * 2.0
    elif pct_from_high >= 20.0:
        return "⚠️ Reduce Allocation", base_pct * 0.5
    else:
        return "🟢 Normal DCA", base_pct * 1.0

# -------------------------------------------------------------------
# DATA FETCHING & DASHBOARD RENDERING
# -------------------------------------------------------------------
st.subheader("Your Dynamic Watchlist & Rules Engine")

data = []
for item in st.session_state.watchlist:
    ticker_symbol = item["ticker"]
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            pct_diff = ((current_price - high_52w) / high_52w) * 100
            
            signal, target_pct = calculate_dca_signal(pct_diff, item["base_pct"])
            suggested_eur = (monthly_budget * target_pct) / 100.0
            
            data.append({
                "Ticker": ticker_symbol,
                "Name": item["name"],
                "Price": f"€{current_price:.2f}",
                "52W High": f"€{high_52w:.2f}",
                "Dist. from High": f"{pct_diff:+.1f}%",
                "Action Signal": signal,
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
            "Target %": f"{item['base_pct']:.1f}%",
            "Suggested €": "N/A"
        })

if data:
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Your watchlist is empty. Use the sidebar to add stocks.")

# -------------------------------------------------------------------
# QUICK TRADE EXECUTION CHECK
# -------------------------------------------------------------------
if st.session_state.watchlist:
    st.markdown("---")
    st.subheader("⚡ Quick Trade Execution Check")
    selected_ticker = st.selectbox("Select stock you are evaluating:", [x["ticker"] for x in st.session_state.watchlist])
    
    for row in data:
        if row["Ticker"] == selected_ticker:
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Status", row["Action Signal"])
            col2.metric("Target Weight", row["Target %"])
            col3.metric("Suggested Amount", row["Suggested €"], delta=row["Dist. from High"])
