import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# -------------------------------------------------------------------
# APP CONFIG & TITLE
# -------------------------------------------------------------------
st.set_page_config(page_title="DCA Strategy Engine", page_icon="📈", layout="centered")
st.title("📈 Strategic DCA Action Center")

# -------------------------------------------------------------------
# CONFIGURATION: STOCKS & BASELINE AMOUNTS
# -------------------------------------------------------------------
# Define your top tickers and standard baseline monthly DCA allocations
WATCHLIST = [
    {"ticker": "PLTR", "name": "Palantir Technologies", "base_dca": 20},
    {"ticker": "NVDA", "name": "Nvidia", "base_dca": 10},
    {"ticker": "TSLA", "name": "Tesla", "base_dca": 5},
    {"ticker": "TSM",  "name": "Taiwan Semi", "base_dca": 10},
]

# Pushover API keys for push notifications (Optional: fill in to receive mobile alerts)
PUSHOVER_USER_KEY = "YOUR_PUSHOVER_USER_KEY"
PUSHOVER_API_TOKEN = "YOUR_PUSHOVER_API_TOKEN"

def send_push_notification(title, message):
    """Sends immediate push notification to your smartphone via Pushover API."""
    if PUSHOVER_USER_KEY != "YOUR_PUSHOVER_USER_KEY":
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message
        })

# -------------------------------------------------------------------
# DCA ENGINE LOGIC
# -------------------------------------------------------------------
def calculate_dca_signal(pct_from_high, base_amount):
    """
    Custom DCA Rules Engine:
    - Down >= 15%: Double Down (Double baseline DCA)
    - Up >= 20%: Reduce Allocation (Half baseline DCA)
    - Otherwise: Normal DCA (Standard baseline)
    """
    if pct_from_high <= -15.0:
        return "🚀 Double Down", base_amount * 2, "off"
    elif pct_from_high >= 20.0:
        return "⚠️ Reduce Allocation", base_amount * 0.5, "warning"
    else:
        return "🟢 Normal DCA", base_amount * 1.0, "normal"

# -------------------------------------------------------------------
# DATA FETCHING & RENDERING
# -------------------------------------------------------------------
st.subheader("Your High-Conviction Watchlist")

data = []
for item in WATCHLIST:
    ticker_symbol = item["ticker"]
    stock = yf.Ticker(ticker_symbol)
    
    # Fetch 1 year of daily history to determine current price and 52-week high
    hist = stock.history(period="1y")
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        high_52w = hist['High'].max()
        pct_diff = ((current_price - high_52w) / high_52w) * 100
        
        signal, suggested_amount, alert_type = calculate_dca_signal(pct_diff, item["base_dca"])
        
        data.append({
            "Stock": f"{ticker_symbol} ({item['name']})",
            "Current Price": f"€{current_price:.2f}",
            "52W High": f"€{high_52w:.2f}",
            "Dist. from High": f"{pct_diff:+.1f}%",
            "Action Signal": signal,
            "Suggested Trade": f"€{suggested_amount:.2f}"
        })

# Display clean interactive UI
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True)

# -------------------------------------------------------------------
# MANUAL EXECUTION QUICK CHECK
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("⚡ Quick Trade Execution Check")
selected_ticker = st.selectbox("Select stock you are about to buy:", [x["ticker"] for x in WATCHLIST])

for item in data:
    if selected_ticker in item["Stock"]:
        st.metric("Recommended Allocation", item["Suggested Trade"], delta=item["Action Signal"])
        st.caption(f"Current Status: **{item['Action Signal']}** ({item['Dist. from High']} relative to 52-week high)")
