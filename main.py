import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ==========================================================
# 1. THE BRAIN: INSTITUTIONAL DATA ENGINE
# ==========================================================
class QuantEngine:
    """Handles 2026 data protocols and high-fidelity technicals."""
    
    @staticmethod
    @st.cache_data(ttl=60)
    def get_market_intelligence(symbol, interval):
        try:
            # Auto-correction for NSE stocks
            ticker = f"{symbol.strip().upper()}"
            if "." not in ticker:
                ticker = f"{ticker}.NS"
            
            # Fetch data with lookback optimized for mobile loading speed
            period = "60d" if interval in ["15m", "1h"] else "max"
            df = yf.download(ticker, interval=interval, period=period, progress=False, auto_adjust=True)
            
            if df.empty:
                return None, symbol
                
            # --- MANDATORY 2026 HEADER REPAIR ---
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # --- TECHNICAL AUDIT CALCULATIONS ---
            # RSI (14 Period)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # VWAP (Cumulative)
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
            
            # EMAs & SMAs
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # High/Low Benchmarks
            df['52W_H'] = df['High'].rolling(window=252, min_periods=1).max()
            df['52W_L'] = df['Low'].rolling(window=252, min_periods=1).min()
            
            return df, ticker
        except Exception as e:
            return None, symbol

# ==========================================================
# 2. THE SKIN: ADVANCED MOBILE CSS
# ==========================================================
st.set_page_config(
    page_title="QuantPro Terminal", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Persistent State Management
if 'page' not in st.session_state: st.session_state.page = "welcome"
if 'active_stock' not in st.session_state: st.session_state.active_stock = "RELIANCE"
if 'history' not in st.session_state: st.session_state.history = ["RELIANCE", "TCS", "ZOMATO"]

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Base Theme */
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Professional Card Component */
    .quant-card {
        background: linear-gradient(145deg, #161b22, #0d1117);
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .quant-label { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .quant-value { color: #58a6ff; font-size: 20px; font-weight: 800; margin-top: 5px; }
    
    /* Touch-Target Sidebar */
    [data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: 600; }

    /* The Hero Button (Massive & Professional) */
    .hero-btn-container > div > button {
        height: 5em !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        letter-spacing: 2px !important;
        background: linear-gradient(90deg, #58a6ff, #1f6feb) !important;
        border: none !important;
        border-radius: 20px !important;
        margin-top: -180px !important;
        box-shadow: 0 15px 45px rgba(31, 111, 235, 0.4) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 3. NAVIGATION LOGIC
# ==========================================================

# --- PAGE 1: WELCOME SCREEN (MOBILE HERO) ---
if st.session_state.page == "welcome":
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="
            height: 85vh; width: 100%;
            background: linear-gradient(rgba(13,17,23,0.3), rgba(13,17,23,0.95)), 
            url('https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?auto=compress&cs=tinysrgb&w=1260');
            background-size: cover; background-position: center;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            border-radius: 30px; border: 1px solid #30363d; text-align: center;
        ">
            <h1 style="font-size: clamp(3rem, 15vw, 7rem); margin:0; font-weight: 900; letter-spacing: -5px; color: white;">QUANTPRO</h1>
            <p style="font-size: 1rem; color: #8b949e; letter-spacing: 3px; font-weight: 400; text-transform: uppercase;">Institutional Intelligence 2026</p>
        </div>
    """, unsafe_allow_html=True)

    _, col_btn, _ = st.columns([0.1, 0.8, 0.1])
    with col_btn:
        st.markdown('<div class="hero-btn-container">', unsafe_allow_html=True)
        if st.button("🚀 START TERMINAL"):
            st.session_state.page = "terminal"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: MAIN TERMINAL (MOBILE UI) ---
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("💎 QuantPro")
    if st.sidebar.button("🏠 Home Screen"):
        st.session_state.page = "welcome"
        st.rerun()
    
    st.sidebar.markdown("---")
    query = st.sidebar.text_input("🔍 Search Asset", value=st.session_state.active_stock).upper()
    timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "1d"])
    
    if st.sidebar.button("⚡ Update Analysis"):
        st.session_state.active_stock = query
        if query not in st.session_state.history: st.session_state.history.append(query)
        st.rerun()
    
    st.sidebar.subheader("Recent")
    for stock in st.session_state.history[-5:]:
        if st.sidebar.button(f"📊 {stock}", key=f"hist_{stock}"):
            st.session_state.active_stock = stock
            st.rerun()

    # --- DATA EXECUTION ---
    engine = QuantEngine()
    df, full_name = engine.get_market_intelligence(st.session_state.active_stock, timeframe)

    if df is not None:
        last, prev = df.iloc[-1], df.iloc[-2]
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        
        # Header Section
        st.title(f"{full_name}")
        st.metric("Price (LTP)", f"₹{last['Close']:,.2f}", f"{change:.2f}%")
        
        # --- MOBILE CARD GRID (Detailed Audit) ---
        st.subheader("📋 Institutional Technical Audit")
        
        # Row 1: Key Levels
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="quant-card"><div class="quant-label">VWAP</div><div class="quant-value">₹{last["VWAP"]:,.1f}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quant-card"><div class="quant-label">EMA 20</div><div class="quant-value">₹{last["EMA_20"]:,.1f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="quant-card"><div class="quant-label">RSI 14</div><div class="quant-value">{last["RSI"]:.1f}</div></div>', unsafe_allow_html=True)
            rsi_text = "OVERBOUGHT" if last['RSI'] > 70 else "OVERSOLD" if last['RSI'] < 30 else "NEUTRAL"
            st.markdown(f'<div class="quant-card"><div class="quant-label">MOMENTUM</div><div class="quant-value" style="font-size:14px;">{rsi_text}</div></div>', unsafe_allow_html=True)

        # Row 2: Range Benchmarks
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f'<div class="quant-card"><div class="quant-label">52W High</div><div class="quant-value">₹{last["52W_H"]:,.1f}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quant-card"><div class="quant-label">SMA 50</div><div class="quant-value">₹{last["SMA_50"]:,.1f}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="quant-card"><div class="quant-label">52W Low</div><div class="quant-value">₹{last["52W_L"]:,.1f}</div></div>', unsafe_allow_html=True)
            vol_m = last['Volume'] / 1_000_000
            st.markdown(f'<div class="quant-card"><div class="quant-label">Volume</div><div class="quant-value">{vol_m:.1f}M</div></div>', unsafe_allow_html=True)

        # --- MOMENTUM CHART ---
        st.subheader("📈 Relative Strength Visualizer")
        
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#58a6ff', width=3), fill='toself', fillcolor='rgba(88, 166, 255, 0.05)'))
        fig.add_hline(y=70, line_dash="dash", line_color="#f85149", annotation_text="OB")
        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", annotation_text="OS")
        
        fig.update_layout(
            template="plotly_dark", height=450, 
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, rangeslider_visible=False),
            yaxis=dict(side="right", range=[0, 100], showgrid=False),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Expander for Full Log
        with st.expander("🔍 Deep Technical Audit Log"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    else:
        st.error(f"Asset '{st.session_state.active_stock}' not found. Ensure it is a valid NSE/BSE ticker.")

st.sidebar.markdown("---")
st.sidebar.caption("QuantPro Terminal v4.0.2 | 2026 Build")
