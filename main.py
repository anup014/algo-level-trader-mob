import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ==========================================================
# 1. CORE DATA ENGINE (SMART SEARCH & QUANT LOGIC)
# ==========================================================
class QuantEnginePro:
    @staticmethod
    @st.cache_data(ttl=60)
    def fetch_market_data(user_input, interval):
        """Auto-corrects searches and repairs 2026 Multi-Index headers."""
        try:
            query = user_input.strip().upper()
            search_list = [query]
            if "." not in query:
                search_list.insert(0, f"{query}.NS")
            
            df = pd.DataFrame()
            final_symbol = query
            for ticker in search_list:
                # Optimized period fetching based on interval choice
                lookback = "60d" if interval in ["15m", "1h"] else "max"
                df = yf.download(ticker, interval=interval, period=lookback, progress=False, auto_adjust=True)
                if not df.empty:
                    final_symbol = ticker
                    break
            
            if df.empty: return None, query

            # 2026 DATA FIX: Flatten Multi-Index columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df.index = pd.to_datetime(df.index)
            return df, final_symbol
        except:
            return None, user_input

    @staticmethod
    def apply_technicals(df):
        """Institutional Logic: RSI, VWAP, EMA, and Yearly Benchmarks."""
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        # VWAP
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        # Trend & Yearly Benchmarks
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['52W_H'] = df['High'].rolling(window=252, min_periods=1).max()
        df['52W_L'] = df['Low'].rolling(window=252, min_periods=1).min()
        
        return df

# ==========================================================
# 2. UI CONFIG & CSS (MOBILE OPTIMIZED)
# ==========================================================
st.set_page_config(page_title="QuantPro Terminal", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

# Initialize State
if 'app_state' not in st.session_state:
    st.session_state.app_state = "welcome"
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["RELIANCE", "TCS", "ZOMATO", "IRFC"]
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = "RELIANCE"

# Global Styles (Dark Theme + Metric Cards)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 15px !important; }
    [data-testid="stMetricValue"] { color: #58a6ff !important; font-weight: 700; font-size: 1.5rem !important; }
    .stSidebar { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    
    /* MOBILE BUTTON STYLING */
    div.stButton > button:first-child {
        height: 4.8em !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        border-radius: 15px !important;
        background: rgba(88, 166, 255, 0.1) !important;
        color: #58a6ff !important;
        border: 2px solid #58a6ff !important;
        backdrop-filter: blur(10px) !important;
        margin-top: -180px; 
        position: relative;
        z-index: 9999;
        transition: all 0.4s ease;
    }
    div.stButton > button:first-child:hover {
        background: #58a6ff !important;
        color: #0d1117 !important;
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(88, 166, 255, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 3. PAGE ROUTING
# ==========================================================

# --- PAGE A: FULL-SCREEN WELCOME SCREEN ---
if st.session_state.app_state == "welcome":
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="
            height: 85vh; width: 100%; 
            background-image: linear-gradient(rgba(13, 17, 23, 0.2), rgba(13, 17, 23, 0.9)), 
            url('https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?auto=compress&cs=tinysrgb&w=1260'); 
            background-size: cover; background-position: center; 
            display: flex; flex-direction: column; justify-content: center; align-items: center; 
            border-radius: 40px; color: white; text-align: center; border: 1px solid #30363d;
        ">
            <h1 style="font-size: clamp(3.5rem, 15vw, 7.5rem); margin-bottom: 0px; font-weight: 900; letter-spacing: -6px; line-height: 0.9;">QUANTPRO</h1>
            <p style="font-size: clamp(1rem, 4vw, 1.5rem); margin-top: 20px; margin-bottom: 80px; opacity: 0.8; letter-spacing: 2px; color: #8b949e; text-transform: uppercase;">
                Institutional Intelligence • 2026 Live Momentum
            </p>
        </div>
    """, unsafe_allow_html=True)

    _, btn_col, _ = st.columns([0.1, 0.8, 0.1]) 
    with btn_col:
        if st.button("🚀 Launch Terminal", use_container_width=True):
            st.session_state.app_state = "terminal"
            st.rerun()

# --- PAGE B: THE TRADING TERMINAL ---
elif st.session_state.app_state == "terminal":
    # Sidebar
    st.sidebar.title("💎 QuantPro")
    if st.sidebar.button("🏠 Home Screen", use_container_width=True):
        st.session_state.app_state = "welcome"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Watchlist")
    for item in st.session_state.watchlist:
        cols = st.sidebar.columns([4, 1])
        if cols[0].button(f"📊 {item}", key=f"nav_{item}", use_container_width=True):
            st.session_state.active_ticker = item
            st.rerun()
        if cols[1].button("✖", key=f"del_{item}"):
            st.session_state.watchlist.remove(item)
            st.rerun()

    st.sidebar.markdown("---")
    new_stock = st.sidebar.text_input("🔍 Search Stock", placeholder="e.g. HDFC").upper()
    if st.sidebar.button("Add & Analyze", use_container_width=True):
        if new_stock:
            if new_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_stock)
            st.session_state.active_ticker = new_stock
            st.rerun()

    # Data Fetching
    engine = QuantEnginePro()
    interval = st.sidebar.selectbox("Interval", ["15m", "1h", "1d"])
    data, ticker_id = engine.fetch_market_data(st.session_state.active_ticker, interval)

    if data is not None:
        df = engine.apply_technicals(data)
        last, prev = df.iloc[-1], df.iloc[-2]
        
        # Dashboard Header
        h1, h2 = st.columns([3, 1])
        h1.title(f"{ticker_id}")
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        h2.metric("LTP", f"₹{last['Close']:,.2f}", f"{change:.2f}%")

        # --- 4 COLUMN AUDIT TABLE ---
        st.subheader("📋 Institutional Technical Audit")
        
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        
        with c1:
            st.markdown("**Price Action**")
            st.metric("Open", f"₹{last['Open']:,.2f}")
            st.metric("High", f"₹{last['High']:,.2f}")
            st.metric("Low", f"₹{last['Low']:,.2f}")
        with c2:
            st.markdown("**Institutional**")
            st.metric("VWAP", f"₹{last['VWAP']:,.2f}")
            st.metric("EMA (20)", f"₹{last['EMA_20']:,.2f}")
            st.metric("SMA (50)", f"₹{last['SMA_50']:,.2f}")
        with c3:
            st.markdown("**Momentum**")
            st.metric("RSI (14)", f"{last['RSI']:.2f}")
            rsi_zone = "Oversold" if last['RSI'] < 30 else "Overbought" if last['RSI'] > 70 else "Neutral"
            st.metric("RSI Zone", rsi_zone)
            st.metric("Volume", f"{int(last['Volume']):,}")
        with c4:
            st.markdown("**Yearly Range**")
            st.metric("52W High", f"₹{last['52W_H']:,.2f}")
            st.metric("52W Low", f"₹{last['52W_L']:,.2f}")
            dist = ((last['52W_H'] - last['Close']) / last['52W_H']) * 100
            st.metric("Off High", f"{dist:.2f}%")

        st.markdown("---")
        
        # Momentum Chart
        st.subheader("Momentum Visualizer (RSI)")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#58a6ff', width=2), fill='toself', fillcolor='rgba(88, 166, 255, 0.05)'))
        fig.add_hline(y=70, line_dash="dash", line_color="#f85149", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", annotation_text="Oversold")
        fig.update_layout(height=450, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                          xaxis=dict(rangeslider_visible=False, showgrid=False), yaxis=dict(side="right", range=[0, 100], showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.error("Connection Error or Invalid Ticker.")

st.sidebar.markdown("---")
st.sidebar.caption("QuantPro v3.0 | Secure Build 2026")
