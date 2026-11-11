import json
import json
import copy
import streamlit as stimport json
import json
import copy
import streamlit as st
from streamlit_local_storage import LocalStorage
from streamlit_local_storage import LocalStorage
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

    /* RED FIX: settings panel styled directly on a keyed container
       (no empty <div> wrapper is rendered any more) */
    .st-key-settings_box {
        background: rgba(16, 22, 34, 0.85);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* PINK FIX (a): forms have no box of their own */
    div[data-testid="stForm"],
    .stForm {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* PINK FIX (b): ONE box per input.
       The outer BaseWeb wrapper owns the fill, stroke and radius;
       every inner layer is made fully transparent with no border. */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        overflow: hidden;
    }
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] > div,
    .stTextInput input,
    .stNumberInput input,
    .stNumberInput button,
    div[data-testid="stNumberInputContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: none !important;
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    div[data-testid="stNumberInputContainer"] {
        border: none !important;
    }

    /* TIMEFRAME PILLS (st.segmented_control): no radio circles exist,
       and the group stretches to the full content width */
    div[data-testid="stElementContainer"]:has(div[data-testid="stButtonGroup"]),
    div[data-testid="stButtonGroup"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    div[data-testid="stButtonGroup"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    div[data-testid="stButtonGroup"] > div,
    div[data-testid="stButtonGroup"] > div > div {
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    div[data-testid="stButtonGroup"] button {
        flex: 1 1 0 !important;
        width: 100% !important;
        min-width: 0 !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 0 !important;
        margin: 0 !important;
        justify-content: center !important;
        box-shadow: none !important;
    }
    div[data-testid="stButtonGroup"] button p {
        color: #ffffff !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    /* Plotly Tooltip: rounded corners (unified-hover box + classic box) */
    .hoverlayer .legend rect.bg,
    .hoverlayer .hovertext rect {
        rx: 8px !important;
        ry: 8px !important;
        fill: rgba(16, 22, 34, 0.9) !important;
        stroke: rgba(255, 255, 255, 0.2) !important;
    }
    /* Date header of the tooltip: bold */
    .hoverlayer .legend .legendtitletext {
        font-weight: 700 !important;
    }

    /* Text & Headers */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SESSION STATE: WATCHLIST & SETTINGS TOGGLE
# -------------------------------------------------------------------
STORAGE_KEY = "doubledown_watchlist"

DEFAULT_WATCHLIST = [
    {"ticker": "PLTR", "name": "Palantir Technologies", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "NVDA", "name": "Nvidia", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "TSLA", "name": "Tesla", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "TSM",  "name": "Taiwan Semi", "dip_threshold": 15.0, "peak_threshold": 20.0},
]

localS = LocalStorage()


def parse_saved(raw):
    """Turn whatever the browser storage returns into a valid watchlist (or None)."""
    try:
        for _ in range(3):  # handles values that were JSON-encoded more than once
            if isinstance(raw, str):
                raw = json.loads(raw)
        if isinstance(raw, list) and raw:
            cleaned = []
            for it in raw:
                cleaned.append({
                    "ticker": str(it["ticker"]),
                    "name": str(it.get("name", it["ticker"])),
                    "dip_threshold": float(it.get("dip_threshold", 15.0)),
                    "peak_threshold": float(it.get("peak_threshold", 20.0)),
                })
            return cleaned
    except Exception:
        pass
    return None


if "watchlist" not in st.session_state:
    st.session_state.watchlist = copy.deepcopy(DEFAULT_WATCHLIST)
if "ls_loaded" not in st.session_state:
    st.session_state.ls_loaded = False
if "save_pending" not in st.session_state:
    st.session_state.save_pending = False
if "save_counter" not in st.session_state:
    st.session_state.save_counter = 0

# Load the saved watchlist from the browser once. The storage component answers
# asynchronously, so the first run may return None and a rerun delivers the value.
if not st.session_state.ls_loaded:
    saved = parse_saved(localS.getItem(STORAGE_KEY))
    if saved:
        st.session_state.watchlist = saved
        st.session_state.ls_loaded = True

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "time_window" not in st.session_state:
    st.session_state.time_window = "6M"

# -------------------------------------------------------------------
# PERSISTENCE: watchlist saved in the phone's browser (localStorage)
# -------------------------------------------------------------------
STORAGE_KEY = "doubledown_watchlist"

for _k, _v in (("ls_loaded", False), ("pending_save", False), ("save_count", 0)):
    if _k not in st.session_state:
        st.session_state[_k] = _v

localS = LocalStorage()

def mark_dirty():
    """Call after any watchlist change; it is written to the browser on the next run."""
    st.session_state.ls_loaded = True
    st.session_state.pending_save = True

# Load once: the browser answers a moment after the first run, then Streamlit reruns
if not st.session_state.ls_loaded:
    try:
        _saved = localS.getItem(STORAGE_KEY)
        if isinstance(_saved, str):
            _saved = json.loads(_saved)
    except Exception:
        _saved = None
    if isinstance(_saved, list) and all(isinstance(x, dict) and "ticker" in x for x in _saved):
        st.session_state.watchlist = _saved
        st.session_state.ls_loaded = True
        st.rerun()

# Write after a change
if st.session_state.pending_save:
    localS.setItem(
        STORAGE_KEY,
        json.dumps(st.session_state.watchlist),
        key=f"save_{st.session_state.save_count}"
    )
    st.session_state.save_count += 1
    st.session_state.pending_save = False

# -------------------------------------------------------------------
# HEADER & INLINE SETTINGS MENU
# -------------------------------------------------------------------
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("📈 DoubleDown DCA")
with col_btn:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

if st.session_state.show_settings:
    # Keyed container -> CSS class "st-key-settings_box" (needs Streamlit >= 1.39)
    with st.container(key="settings_box"):
        st.subheader("Settings & Watchlist")

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
                    mark_dirty()
                    st.session_state.save_pending = True
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
                            mark_dirty()
                            st.session_state.save_pending = True
                            st.success(f"Updated {edit_ticker} thresholds!")
                            st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Remove Stock")
        tickers_to_remove = [item["ticker"] for item in st.session_state.watchlist]
        selected_to_remove = st.selectbox("Select ticker to remove", tickers_to_remove if tickers_to_remove else ["None"], key="remove_select")
        if st.button("Remove Selected") and tickers_to_remove:
            st.session_state.watchlist = [item for item in st.session_state.watchlist if item["ticker"] != selected_to_remove]
            mark_dirty()
            st.session_state.save_pending = True
            st.success(f"Removed {selected_to_remove}!")
            st.rerun()

# -------------------------------------------------------------------
# SAVE TO BROWSER STORAGE (runs on the rerun right after a change)
# -------------------------------------------------------------------
if st.session_state.save_pending:
    st.session_state.save_counter += 1
    st.session_state.ls_loaded = True
    localS.setItem(
        STORAGE_KEY,
        json.dumps(st.session_state.watchlist),
        key=f"save_watchlist_{st.session_state.save_counter}",
    )
    st.session_state.save_pending = False

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
if st.session_state.watchlist and data:
    st.markdown("---")
    st.subheader("⚡ Quick Trade Execution Check & Chart")
    selected_ticker = st.selectbox("Select stock to analyze:", [x["Ticker"] for x in data], key="chart_select")

    for row in data:
        if row["Ticker"] == selected_ticker:
            st.metric("Current Status", row["Action Signal"], delta=row["Dist. from High"])

            if selected_ticker in history_cache:
                full_hist = history_cache[selected_ticker]

                # Active line color pre-calculation
                current_tw = st.session_state.get("time_window") or "6M"
                now_temp = full_hist.index[-1]
                if current_tw == "1W": start_d = now_temp - timedelta(days=7)
                elif current_tw == "1M": start_d = now_temp - timedelta(days=30)
                elif current_tw == "3M": start_d = now_temp - timedelta(days=90)
                elif current_tw == "6M": start_d = now_temp - timedelta(days=180)
                elif current_tw == "YTD": start_d = pd.Timestamp(now_temp.year, 1, 1, tz=now_temp.tz) if now_temp.tz else pd.Timestamp(now_temp.year, 1, 1)
                elif current_tw == "3Y": start_d = now_temp - timedelta(days=365*3)
                else: start_d = full_hist.index[0]

                df_t = full_hist[full_hist.index >= start_d]
                if df_t.empty: df_t = full_hist.tail(10)
                active_line_color = "#3fb950" if df_t['Close'].iloc[-1] >= df_t['Close'].mean() else "#f85149"

                # Style selected timeframe pill with trend color
                st.markdown(f"""
                    <style>
                    div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"],
                    div[data-testid="stButtonGroup"] button[aria-checked="true"],
                    div[data-testid="stButtonGroup"] button[aria-pressed="true"],
                    div[data-testid="stButtonGroup"] button[aria-selected="true"],
                    div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {{
                        background: {active_line_color} !important;
                        background-color: {active_line_color} !important;
                        border-color: {active_line_color} !important;
                    }}
                    div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] *,
                    div[data-testid="stButtonGroup"] button[aria-checked="true"] *,
                    div[data-testid="stButtonGroup"] button[aria-pressed="true"] *,
                    div[data-testid="stButtonGroup"] button[aria-selected="true"] *,
                    div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"] * {{
                        color: #000000 !important;
                        font-weight: 700 !important;
                    }}
                    </style>
          
from streamlit_local_storage import LocalStorage
from streamlit_local_storage import LocalStorage
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

    /* RED FIX: settings panel styled directly on a keyed container
       (no empty <div> wrapper is rendered any more) */
    .st-key-settings_box {
        background: rgba(16, 22, 34, 0.85);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* PINK FIX (a): forms have no box of their own */
    div[data-testid="stForm"],
    .stForm {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* PINK FIX (b): ONE box per input.
       The outer BaseWeb wrapper owns the fill, stroke and radius;
       every inner layer is made fully transparent with no border. */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        overflow: hidden;
    }
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] > div,
    .stTextInput input,
    .stNumberInput input,
    .stNumberInput button,
    div[data-testid="stNumberInputContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: none !important;
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    div[data-testid="stNumberInputContainer"] {
        border: none !important;
    }

    /* TIMEFRAME PILLS (st.segmented_control): no radio circles exist,
       and the group stretches to the full content width */
    div[data-testid="stElementContainer"]:has(div[data-testid="stButtonGroup"]),
    div[data-testid="stButtonGroup"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    div[data-testid="stButtonGroup"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    div[data-testid="stButtonGroup"] > div,
    div[data-testid="stButtonGroup"] > div > div {
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    div[data-testid="stButtonGroup"] button {
        flex: 1 1 0 !important;
        width: 100% !important;
        min-width: 0 !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 0 !important;
        margin: 0 !important;
        justify-content: center !important;
        box-shadow: none !important;
    }
    div[data-testid="stButtonGroup"] button p {
        color: #ffffff !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    /* Plotly Tooltip: rounded corners (unified-hover box + classic box) */
    .hoverlayer .legend rect.bg,
    .hoverlayer .hovertext rect {
        rx: 8px !important;
        ry: 8px !important;
        fill: rgba(16, 22, 34, 0.9) !important;
        stroke: rgba(255, 255, 255, 0.2) !important;
    }
    /* Date header of the tooltip: bold */
    .hoverlayer .legend .legendtitletext {
        font-weight: 700 !important;
    }

    /* Text & Headers */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# SESSION STATE: WATCHLIST & SETTINGS TOGGLE
# -------------------------------------------------------------------
STORAGE_KEY = "doubledown_watchlist"

DEFAULT_WATCHLIST = [
    {"ticker": "PLTR", "name": "Palantir Technologies", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "NVDA", "name": "Nvidia", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "TSLA", "name": "Tesla", "dip_threshold": 15.0, "peak_threshold": 20.0},
    {"ticker": "TSM",  "name": "Taiwan Semi", "dip_threshold": 15.0, "peak_threshold": 20.0},
]

localS = LocalStorage()


def parse_saved(raw):
    """Turn whatever the browser storage returns into a valid watchlist (or None)."""
    try:
        for _ in range(3):  # handles values that were JSON-encoded more than once
            if isinstance(raw, str):
                raw = json.loads(raw)
        if isinstance(raw, list) and raw:
            cleaned = []
            for it in raw:
                cleaned.append({
                    "ticker": str(it["ticker"]),
                    "name": str(it.get("name", it["ticker"])),
                    "dip_threshold": float(it.get("dip_threshold", 15.0)),
                    "peak_threshold": float(it.get("peak_threshold", 20.0)),
                })
            return cleaned
    except Exception:
        pass
    return None


if "watchlist" not in st.session_state:
    st.session_state.watchlist = copy.deepcopy(DEFAULT_WATCHLIST)
if "ls_loaded" not in st.session_state:
    st.session_state.ls_loaded = False
if "save_pending" not in st.session_state:
    st.session_state.save_pending = False
if "save_counter" not in st.session_state:
    st.session_state.save_counter = 0

# Load the saved watchlist from the browser once. The storage component answers
# asynchronously, so the first run may return None and a rerun delivers the value.
if not st.session_state.ls_loaded:
    saved = parse_saved(localS.getItem(STORAGE_KEY))
    if saved:
        st.session_state.watchlist = saved
        st.session_state.ls_loaded = True

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "time_window" not in st.session_state:
    st.session_state.time_window = "6M"

# -------------------------------------------------------------------
# PERSISTENCE: watchlist saved in the phone's browser (localStorage)
# -------------------------------------------------------------------
STORAGE_KEY = "doubledown_watchlist"

for _k, _v in (("ls_loaded", False), ("pending_save", False), ("save_count", 0)):
    if _k not in st.session_state:
        st.session_state[_k] = _v

localS = LocalStorage()

def mark_dirty():
    """Call after any watchlist change; it is written to the browser on the next run."""
    st.session_state.ls_loaded = True
    st.session_state.pending_save = True

# Load once: the browser answers a moment after the first run, then Streamlit reruns
if not st.session_state.ls_loaded:
    try:
        _saved = localS.getItem(STORAGE_KEY)
        if isinstance(_saved, str):
            _saved = json.loads(_saved)
    except Exception:
        _saved = None
    if isinstance(_saved, list) and all(isinstance(x, dict) and "ticker" in x for x in _saved):
        st.session_state.watchlist = _saved
        st.session_state.ls_loaded = True
        st.rerun()

# Write after a change
if st.session_state.pending_save:
    localS.setItem(
        STORAGE_KEY,
        json.dumps(st.session_state.watchlist),
        key=f"save_{st.session_state.save_count}"
    )
    st.session_state.save_count += 1
    st.session_state.pending_save = False

# -------------------------------------------------------------------
# HEADER & INLINE SETTINGS MENU
# -------------------------------------------------------------------
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.title("📈 DoubleDown DCA")
with col_btn:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

if st.session_state.show_settings:
    # Keyed container -> CSS class "st-key-settings_box" (needs Streamlit >= 1.39)
    with st.container(key="settings_box"):
        st.subheader("Settings & Watchlist")

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
                    mark_dirty()
                    st.session_state.save_pending = True
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
                            mark_dirty()
                            st.session_state.save_pending = True
                            st.success(f"Updated {edit_ticker} thresholds!")
                            st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Remove Stock")
        tickers_to_remove = [item["ticker"] for item in st.session_state.watchlist]
        selected_to_remove = st.selectbox("Select ticker to remove", tickers_to_remove if tickers_to_remove else ["None"], key="remove_select")
        if st.button("Remove Selected") and tickers_to_remove:
            st.session_state.watchlist = [item for item in st.session_state.watchlist if item["ticker"] != selected_to_remove]
            mark_dirty()
            st.session_state.save_pending = True
            st.success(f"Removed {selected_to_remove}!")
            st.rerun()

# -------------------------------------------------------------------
# SAVE TO BROWSER STORAGE (runs on the rerun right after a change)
# -------------------------------------------------------------------
if st.session_state.save_pending:
    st.session_state.save_counter += 1
    st.session_state.ls_loaded = True
    localS.setItem(
        STORAGE_KEY,
        json.dumps(st.session_state.watchlist),
        key=f"save_watchlist_{st.session_state.save_counter}",
    )
    st.session_state.save_pending = False

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
if st.session_state.watchlist and data:
    st.markdown("---")
    st.subheader("⚡ Quick Trade Execution Check & Chart")
    selected_ticker = st.selectbox("Select stock to analyze:", [x["Ticker"] for x in data], key="chart_select")

    for row in data:
        if row["Ticker"] == selected_ticker:
            st.metric("Current Status", row["Action Signal"], delta=row["Dist. from High"])

            if selected_ticker in history_cache:
                full_hist = history_cache[selected_ticker]

                # Active line color pre-calculation
                current_tw = st.session_state.get("time_window") or "6M"
                now_temp = full_hist.index[-1]
                if current_tw == "1W": start_d = now_temp - timedelta(days=7)
                elif current_tw == "1M": start_d = now_temp - timedelta(days=30)
                elif current_tw == "3M": start_d = now_temp - timedelta(days=90)
                elif current_tw == "6M": start_d = now_temp - timedelta(days=180)
                elif current_tw == "YTD": start_d = pd.Timestamp(now_temp.year, 1, 1, tz=now_temp.tz) if now_temp.tz else pd.Timestamp(now_temp.year, 1, 1)
                elif current_tw == "3Y": start_d = now_temp - timedelta(days=365*3)
                else: start_d = full_hist.index[0]

                df_t = full_hist[full_hist.index >= start_d]
                if df_t.empty: df_t = full_hist.tail(10)
                active_line_color = "#3fb950" if df_t['Close'].iloc[-1] >= df_t['Close'].mean() else "#f85149"

                # Style selected timeframe pill with trend color
                st.markdown(f"""
                    <style>
                    div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"],
                    div[data-testid="stButtonGroup"] button[aria-checked="true"],
                    div[data-testid="stButtonGroup"] button[aria-pressed="true"],
                    div[data-testid="stButtonGroup"] button[aria-selected="true"],
                    div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {{
                        background: {active_line_color} !important;
                        background-color: {active_line_color} !important;
                        border-color: {active_line_color} !important;
                    }}
                    div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] *,
                    div[data-testid="stButtonGroup"] button[aria-checked="true"] *,
                    div[data-testid="stButtonGroup"] button[aria-pressed="true"] *,
                    div[data-testid="stButtonGroup"] button[aria-selected="true"] *,
                    div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"] * {{
                        color: #000000 !important;
                        font-weight: 700 !important;
                    }}
                    </style>
          
