import streamlit as st
import pandas as pd
import plotly.express as px
import time
from database import get_db_connection

st.set_page_config(page_title="CRYPTO ALPHA | TERMINAL", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Bloomberg-style Terminal
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #00FF41; }
    .stMetric { background-color: #1A1C24; padding: 15px; border-radius: 10px; border: 1px solid #2D3139; }
    .stDataFrame { border: 1px solid #2D3139; }
    h1, h2, h3 { font-family: 'Courier New', Courier, monospace; color: #00FF41 !important; }
    .css-1offfwp { background-color: #1A1C24 !important; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    try:
        conn = get_db_connection()
        df_transfers = pd.read_sql_query("SELECT * FROM transfers", conn)
        df_signals = pd.read_sql_query("SELECT * FROM ai_signals", conn)
        conn.close()
        
        if not df_transfers.empty:
            df_transfers['timestamp'] = pd.to_datetime(df_transfers['timestamp'])
        if not df_signals.empty:
            df_signals['timestamp'] = pd.to_datetime(df_signals['timestamp'])
            
        return df_transfers, df_signals
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- HEADER ---
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.title("🏹 CRYPTO QUANT TERMINAL")
    st.markdown("`MULTIMODAL QUANT ENGINE | LIVE FEED`")
with c_head2:
    st.markdown(f"**STATUS:** 🟢 ONLINE")
    st.markdown(f"**SERVER TIME:** {time.strftime('%H:%M:%S')}")

# --- DATA LOAD ---
df_t, df_s = load_data()

if not df_t.empty:
    # --- TOP METRICS ---
    st.markdown("### 📊 SYSTEM PERFORMANCE")
    m1, m2, m3, m4 = st.columns(4)
    
    total_vol = df_t['amount_usd'].sum()
    m1.metric("TOTAL FLOW VOLUME", f"${total_vol/1e6:.2f}M")
    
    if not df_s.empty:
        finished = df_s[df_s['status'] != 'PENDING']
        wr = (len(finished[finished['status'] == 'WIN']) / len(finished) * 100) if len(finished) > 0 else 0
        m2.metric("SIGNAL WIN RATE", f"{wr:.1f}%")
        m3.metric("TOTAL SIGNALS", len(df_s))
        m4.metric("PENDING BACKTESTS", len(df_s[df_s['status'] == 'PENDING']))
    else:
        m2.metric("SIGNAL WIN RATE", "0.0%")
        m3.metric("TOTAL SIGNALS", "0")
        m4.metric("PENDING BACKTESTS", "0")

    st.divider()

    # --- MAIN ENGINE VIEWS ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### 🤖 SIGNAL TERMINAL")
        if not df_s.empty:
            def style_status(val):
                if val == 'WIN': return 'color: #00FF41; font-weight: bold'
                if val == 'LOSS': return 'color: #FF3131; font-weight: bold'
                return 'color: #888888'

            sig_disp = df_s.sort_values(by='timestamp', ascending=False).head(15)
            st.dataframe(sig_disp[['timestamp', 'token', 'signal', 'confidence', 'entry_price', 'status']]
                         .style.map(style_status, subset=['status']), use_container_width=True)
        else:
            st.info("ENGINE SCANNING FOR ALPHA...")

        st.markdown("### 🐋 REAL-TIME WHALE ACTIVITY")
        fig = px.scatter(df_t, x='timestamp', y='amount_usd', color='token_name',
                        size='amount_usd', hover_data=['direction', 'sentiment'],
                        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### 🚨 HIGH-ALPHA ALERTS")
        def style_sent(val):
            if val == 'Bullish': return 'background-color: rgba(0, 255, 65, 0.1)'
            if val == 'Bearish': return 'background-color: rgba(255, 49, 49, 0.1)'
            return ''

        recent_alerts = df_t.sort_values(by='timestamp', ascending=False).head(20)
        st.dataframe(recent_alerts[['token_name', 'direction', 'amount_usd', 'sentiment']]
                     .style.map(style_sent, subset=['sentiment'])
                     .format({"amount_usd": "${:,.0f}"}), use_container_width=True)

        st.markdown("### 📦 TOKEN DOMINANCE")
        fig_pie = px.pie(df_t, names='token_name', values='amount_usd', hole=0.6, template="plotly_dark")
        fig_pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- AUTO REFRESH ---
    time.sleep(10)
    st.rerun()

else:
    st.warning("🏹 INITIALIZING MULTIMODAL PIPELINE... WAITING FOR DATA.")
    time.sleep(5)
    st.rerun()
