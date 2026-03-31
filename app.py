import streamlit as st
import yfinance as yf
import os
from groq import Groq
import plotly.graph_objects as go

# ========================
# 🔑 API KEY
# ========================
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found.")
    st.stop()

client = Groq(api_key=api_key)

# ========================
# 🌍 USD → INR
# ========================
def get_rate():
    try:
        return yf.Ticker("INR=X").history(period="1d")["Close"].iloc[-1]
    except:
        return 83

# ========================
# 📊 STOCK DATA
# ========================
def get_stock(symbol):
    try:
        data = yf.Ticker(symbol).history(period="2d")
        rate = get_rate()

        curr = data["Close"].iloc[-1] * rate
        prev = data["Close"].iloc[-2] * rate

        change = curr - prev
        percent = (change / prev) * 100

        return curr, change, percent
    except:
        return None, None, None

# ========================
# 🪙 GOLD PRICE (FIXED)
# ========================
def get_gold_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")

        usd_per_ounce = data["Close"].iloc[-1]
        rate = get_rate()

        inr_per_ounce = usd_per_ounce * rate
        inr_per_gram = inr_per_ounce / 28.35

        return (
            f"🪙 Gold Price:\n"
            f"₹{inr_per_gram:,.0f} per gram\n"
            f"₹{inr_per_ounce:,.0f} per ounce"
        )
    except:
        return "Error fetching gold price"

# ========================
# 📈 CHART
# ========================
def get_chart(symbol, period):
    try:
        data = yf.Ticker(symbol).history(period=period)
        rate = get_rate()

        data[["Open", "High", "Low", "Close"]] *= rate

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"]
        ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500
        )

        return fig
    except:
        return None

# ========================
# 🤖 AI
# ========================
def ask_ai(q, context=None):
    prompt = f"{q}\n\nData:\n{context}" if context else q

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

# ========================
# 🎨 UI
# ========================
st.set_page_config(layout="wide", page_title="Trading Dashboard")
st.title("📊 Zerodha-Style AI Trading Dashboard")

# ========================
# 💼 PORTFOLIO
# ========================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

st.sidebar.title("💼 Portfolio")

sym = st.sidebar.text_input("Stock Symbol")
qty = st.sidebar.number_input("Quantity", min_value=1)

if st.sidebar.button("Add Stock") and sym:
    price, _, _ = get_stock(sym.upper())
    if price:
        st.session_state.portfolio[sym.upper()] = {
            "qty": qty,
            "buy": price
        }

# ========================
# 📊 KPI
# ========================
col1, col2, col3 = st.columns(3)

total_val = 0
total_inv = 0

for s, d in st.session_state.portfolio.items():
    curr, _, _ = get_stock(s)
    if curr:
        total_val += curr * d["qty"]
        total_inv += d["buy"] * d["qty"]

pnl = total_val - total_inv
percent = (pnl / total_inv * 100) if total_inv else 0

col1.metric("💰 Portfolio Value", f"₹{total_val:,.0f}")
col2.metric("📈 Profit / Loss", f"₹{pnl:,.0f}", f"{percent:.2f}%")
col3.metric("📊 Holdings", len(st.session_state.portfolio))

st.markdown("---")

# ========================
# 📋 HOLDINGS
# ========================
st.subheader("📋 Holdings")

for s, d in st.session_state.portfolio.items():
    curr, change, pct = get_stock(s)

    if curr:
        value = curr * d["qty"]
        pnl = value - (d["buy"] * d["qty"])

        color = "🟢" if pnl >= 0 else "🔴"

        st.write(
            f"{color} {s} | ₹{value:,.0f} | P&L: ₹{pnl:,.0f} ({pct:.2f}%)"
        )

st.markdown("---")

# ========================
# 📈 CHART
# ========================
st.subheader("📈 Chart")

symbol = st.text_input("Enter stock for chart (AAPL)")
timeframe = st.radio("Timeframe", ["1d", "5d", "1mo", "6mo"])

if symbol:
    fig = get_chart(symbol.upper(), timeframe)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ========================
# 🤖 CHAT
# ========================
st.subheader("🤖 AI Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = []

for m in st.session_state.chat:
    st.chat_message(m["role"]).write(m["content"])

user = st.chat_input("Ask about stocks or gold...")

if user:
    st.chat_message("user").write(user)
    st.session_state.chat.append({"role": "user", "content": user})

    context = None

    if "gold" in user.lower():
        context = get_gold_price()
    else:
        for w in user.upper().split():
            price, _, _ = get_stock(w)
            if price:
                context = f"{w} price ₹{price:,.0f}"
                break

    reply = ask_ai(user, context)

    st.chat_message("assistant").write(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})