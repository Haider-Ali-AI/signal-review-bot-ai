import streamlit as st
import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from trade_auditor import TradeAuditor

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

st.set_page_config(page_title="AI Trade Calculator", page_icon="🧮", layout="wide")

st.title("🧮 AI Trade Calculator & Reviewer")
st.markdown("Enter your trade plan to check math, calculate position size, and get AI risks advice.")

def get_auditor():
    api_key = os.getenv("OPENAI_API_KEY")
    return TradeAuditor(api_key=api_key)

auditor = get_auditor()

# Sidebar for Capital & Risk
with st.sidebar:
    st.header("Money Management")
    capital = st.number_input("Account Capital ($)", value=10000.0, step=100.0)
    risk_pct = st.number_input("Risk per Trade (%)", value=1.0, step=0.1, min_value=0.1, max_value=100.0)
    
    st.info(f"Risk Amount: **${capital * (risk_pct/100):.2f}**")

# Main Form
with st.form("calculator_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        entry = st.number_input("Entry Price", value=0.0, step=0.0001, format="%.4f")
    with c2:
        sl = st.number_input("Stop Loss", value=0.0, step=0.0001, format="%.4f")
    
    st.subheader("Take Profit Targets")
    t1, t2, t3 = st.columns(3)
    with t1:
        tp1 = st.number_input("TP 1 (Required)", value=0.0, step=0.0001, format="%.4f")
    with t2:
        tp2 = st.number_input("TP 2 (Optional)", value=0.0, step=0.0001, format="%.4f")
    with t3:
        tp3 = st.number_input("TP 3 (Optional)", value=0.0, step=0.0001, format="%.4f")
        
    concern = st.text_area("Constraints / Concerns / Questions", placeholder="e.g. Is this SL too tight?")
    
    submitted = st.form_submit_button("Calculated & Review")

if submitted:
    if entry == 0 or sl == 0 or tp1 == 0:
        st.error("Entry, Stop Loss, and at least TP1 are required.")
    else:
        with st.spinner("Crunching numbers and consulting AI..."):
            tps = [tp1, tp2, tp3]
            result = asyncio.run(auditor.audit_trade(
                entry=entry, sl=sl, tps=tps, capital=capital, risk_pct=risk_pct, user_concern=concern
            ))
        
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            calc = result["calc"]
            verdict = result["verdict"]
            targets = result["targets"]
            advisor = result.get("advisor_response")
            
            # --- DISPLAY RESULTS ---
            
            # 1. Position Sizing
            st.divider()
            st.subheader("🏁 Position Sizing")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Risk Amount", f"${calc['risk_amount']}")
            m2.metric("Units to Buy/Sell", f"{calc['units']:.4f}")
            m3.metric("Total Position Value", f"${calc['position_value']:.2f}")
            m4.metric("Risk/Reward (Max)", result['max_rr'])
            
            # 2. Targets Table
            st.subheader("🎯 Targets Breakdown")
            df = pd.DataFrame(targets)
            if not df.empty:
                # Format for display
                df_display = df.copy()
                df_display['price'] = df_display['price'].apply(lambda x: f"{x:.4f}")
                df_display['profit'] = df_display['profit'].apply(lambda x: f"${x:.2f}")
                df_display['roi'] = df_display['roi'].apply(lambda x: f"{x:.2f}%")
                st.table(df_display)
            
            # 3. Verdict & AI
            st.divider()
            c_verdict, c_ai = st.columns([1, 2])
            
            with c_verdict:
                color = "green" if "MASSIVE" in verdict or "SUPER" in verdict else "orange" if "GOOD" in verdict else "red"
                st.markdown(f"### Verdict")
                st.markdown(f":{color}[## {verdict}]")
            
            with c_ai:
                st.subheader("🤖 AI Mentor Advice")
                st.markdown(advisor)
