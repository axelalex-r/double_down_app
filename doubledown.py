import json
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
                """, unsafe_allow_html=True)

                seg_kwargs = dict(
                    default="6M",
                    selection_mode="single",
                    label_visibility="collapsed",
                    key="time_window"
                )
                try:
                    selected_tw = st.segmented_control(
                        "Time Window", ["1W", "1M", "3M", "6M", "YTD", "3Y"],
                        width="stretch", **seg_kwargs
                    )
                except TypeError:  # older Streamlit without the width argument
                    selected_tw = st.segmented_control(
                        "Time Window", ["1W", "1M", "3M", "6M", "YTD", "3Y"],
                        **seg_kwargs
                    )
                # Clicking the active pill again deselects it -> fall back to 6M
                time_window = selected_tw or "6M"

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

                # Height 240px, minimalist layout
                fig.update_xaxes(hoverformat='%b %d, %Y')
                fig.update_layout(
                    plot_bgcolor='#000000',
                    paper_bgcolor='#000000',
                    font_color='#ffffff',
                    font_family='Space Grotesk',
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=240,
                    xaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(visible=False, showgrid=False, zeroline=False, showticklabels=False),
                    hovermode='x unified',
                    dragmode=False,
                    hoverlabel=dict(
                        bgcolor='rgba(16, 22, 34, 0.85)',
                        bordercolor='rgba(255, 255, 255, 0.2)',
                        font=dict(family='Space Grotesk', color='#ffffff', size=13)
                    )
                )

                fig.update_traces(
                    line=dict(color=line_color, width=2.5),
                    hovertemplate='%{y:.2f} €<extra></extra>'
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
                
