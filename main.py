import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ==========================================================
# 1. INSTITUTIONAL DATA ENGINE
# ==========================================================
class QuantEnginePro:
    @staticmethod
    @st.cache_data(ttl=60)
    def fetch_market_data(user_input, interval):
        try:
            # Clean the input: "HDFC Bank" -> "HDFCBANK"
            raw_query = user_input.strip().upper().replace(" ", "")
            
            # List of attempts: NSE first, then BSE, then raw
            search_list = [f"{raw_query}.NS", f"{raw_query}.BO", raw_query]
            
            df = pd.DataFrame()
            final_symbol = user_input.upper()
            
            for ticker in search_list:
                lookback = "60d" if interval in ["15m", "1h"] else "max"
                df = yf.download(ticker, interval=interval, period=lookback, progress=False, auto_adjust=True)
                if not df.empty:
                    final_symbol = ticker
                    break
            
            if df.empty: return None, user_input
            
            # 2026 Header Fix
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Technical Calculations
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['52W_H'] = df['High'].rolling(window=252, min_periods=1).max()
            df['52W_L'] = df['Low'].rolling(window=252, min_periods=1).min()
            
            return df, final_symbol
        except:
            return None, user_input

# ==========================================================
# 2. MOBILE-FIRST UI CONFIG & CSS
# ==========================================================
st.set_page_config(page_title="Algo Level Trader", layout="wide", initial_sidebar_state="collapsed")

if 'app_state' not in st.session_state:
    st.session_state.app_state = "welcome"
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = "RELIANCE"

# INJECTING PROFESSIONAL MOBILE CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* MOBILE CARD ARCHITECTURE */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
        padding: 10px 0;
    }
    
    .q-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px;
        text-align: left;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .q-icon { font-size: 18px; margin-bottom: 8px; color: #58a6ff; }
    .q-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    .q-value { font-size: 16px; color: #ffffff; font-weight: 700; margin-top: 2px; }

    /* MOBILE-READY BUTTONS */
    div.stButton > button:first-child {
        height: 3.8rem !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #58a6ff, #1f6feb) !important;
        color: white !important;
        border: none !important;
        margin-top: -120px !important;
        box-shadow: 0 10px 30px rgba(31, 111, 235, 0.3) !important;
        transition: transform 0.2s;
    }
    
    /* SIDEBAR MOBILE TWEAKS */
    [data-testid="stSidebar"] { width: 280px !important; border-right: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 3. APP LOGIC FLOW
# ==========================================================

# --- PAGE A: WELCOME (MOBILE SPLASH) ---
if st.session_state.app_state == "welcome":
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="height: 80vh; width: 100%; border-radius: 30px; border: 1px solid #30363d;
            background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.9)), 
            url('https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?auto=compress&cs=tinysrgb&w=1260');
            background-size: cover; background-position: center;
            display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 20px;">
            <h1 style="font-size: clamp(2.5rem, 12vw, 6rem); font-weight: 800; letter-spacing: -3px; color: white; margin:0;">ALGO TRADER</h1>
            <p style="font-size: 0.9rem; color: #8b949e; letter-spacing: 2px; text-transform: uppercase; margin-top: 10px;">Professional Terminal v4.0</p>
        </div>
    """, unsafe_allow_html=True)

    _, btn_col, _ = st.columns([0.1, 0.8, 0.1])
    with btn_col:
        if st.button("🚀 START ANALYSIS"):
            st.session_state.app_state = "terminal"
            st.rerun()

# --- PAGE B: TERMINAL (MAIN APP) ---
else:
   st.sidebar.markdown("### 🔍 Smart Search")
    # This captures the name and updates the session state
    user_search = st.sidebar.text_input(
        "Enter Company Name", 
        value=st.session_state.active_ticker,
        placeholder="e.g. Reliance, TCS, Tata Motors"
    ).upper()
    
    if user_search != st.session_state.active_ticker:
        st.session_state.active_ticker = user_search
        st.rerun()

    interval = st.sidebar.selectbox("Select Timeframe", ["15m", "1h", "1d"])
    
    # FETCH DATA
    engine = QuantEnginePro()
    df, full_name = engine.fetch_market_data(st.session_state.active_ticker, interval)

    if df is not None:
        last, prev = df.iloc[-1], df.iloc[-2]
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        color = "#3fb950" if change >= 0 else "#f85149"
        
        # Header (Scales for Mobile)
        st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <h2 style="margin:0; font-size: 24px;">{full_name}</h2>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size: 28px; font-weight: 800; color: #ffffff;">₹{last['Close']:,.2f}</span>
                    <span style="font-size: 16px; font-weight: 600; color: {color};">{"▲" if change >=0 else "▼"} {abs(change):.2f}%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- MOBILE OPTIMIZED CARD GRID ---
        st.markdown("### 📋 Market Intelligence")
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="q-card">
                <div class="q-icon">📊</div>
                <div class="q-label">VWAP</div>
                <div class="q-value">₹{last['VWAP']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">⚡</div>
                <div class="q-label">RSI (14)</div>
                <div class="q-value">{last['RSI']:.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">📈</div>
                <div class="q-label">EMA 20</div>
                <div class="q-value">₹{last['EMA_20']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">📅</div>
                <div class="q-label">SMA 50</div>
                <div class="q-value">₹{last['SMA_50']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">🏆</div>
                <div class="q-label">52W High</div>
                <div class="q-value">₹{last['52W_H']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">📉</div>
                <div class="q-label">52W Low</div>
                <div class="q-value">₹{last['52W_L']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">🔥</div>
                <div class="q-label">Day High</div>
                <div class="q-value">₹{last['High']:,.1f}</div>
            </div>
            <div class="q-card">
                <div class="q-icon">📦</div>
                <div class="q-label">Volume</div>
                <div class="q-value">{int(last['Volume']):,}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- CHART SECTION ---
        st.markdown("### 📈 Momentum Chart")
        
        fig = go.Figure(data=[go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#58a6ff', width=3), fill='toself', fillcolor='rgba(88,166,255,0.05)')])
        fig.add_hline(y=70, line_dash="dash", line_color="#f85149")
        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950")
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=10, b=0),
                          xaxis=dict(showgrid=False), yaxis=dict(side="right", showgrid=False, range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Deep Audit Expander
        with st.expander("📝 View Full Audit Log"):
            st.dataframe(df.sort_index(ascending=False).head(50), use_container_width=True)
    else:
        st.error("Invalid Ticker or Search Error. Please try again.")

st.sidebar.markdown("---")
st.sidebar.caption("Algo Level Trader Mobile • Build 2026")
