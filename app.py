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
def get_usd_to_inr():
    try:
        return yf.Ticker("INR=X").history(period="1d")["Close"].iloc[-1]
    except:
        return 83


# ========================
# 📊 STOCK PRICE
# ========================
def get_stock_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="2d")
        rate = get_usd_to_inr()

        latest = data["Close"].iloc[-1] * rate
        prev = data["Close"].iloc[-2] * rate

        change = latest - prev
        percent = (change / prev) * 100

        return latest, change, percent
    except:
        return None, None, None


# ========================
# 📈 CHART (ZERODHA STYLE)
# ========================
def plot_chart(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1mo")
        rate = get_usd_to_inr()

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
            title=f"{symbol} Chart (INR)",
            xaxis_rangeslider_visible=False
        )

        return fig
    except:
        return None


# ========================
# 🤖 AI
# ========================
def ask_ai(query, context=None):
    try:
        prompt = f"{query}\n\nData:\n{context}" if context else query

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
    except:
        return "Error"


# ========================
# 🎨 UI
# ========================
st.set_page_config(page_title="Market Dashboard", page_icon="📈")
st.title("📊 AI Market Dashboard (Pro)")

# ========================
# 💼 PORTFOLIO
# ========================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

st.sidebar.header("💼 Portfolio")

sym = st.sidebar.text_input("Stock (AAPL)")
qty = st.sidebar.number_input("Qty", min_value=1)

if st.sidebar.button("Add") and sym:
    price, _, _ = get_stock_data(sym.upper())
    if price:
        st.session_state.portfolio[sym.upper()] = {
            "qty": qty,
            "buy_price": price
        }

# ========================
# 💰 DASHBOARD
# ========================
st.subheader("📊 Portfolio Overview")

total_value = 0
total_investment = 0

for sym, data in st.session_state.portfolio.items():
    current, change, percent = get_stock_data(sym)

    if current:
        value = current * data["qty"]
        investment = data["buy_price"] * data["qty"]

        pnl = value - investment
        pnl_percent = (pnl / investment) * 100

        total_value += value
        total_investment += investment

        color = "🟢" if pnl >= 0 else "🔴"

        st.write(
            f"{color} {sym} | Value: ₹{value:,.0f} | P&L: ₹{pnl:,.0f} ({pnl_percent:.2f}%)"
        )

# TOTAL
if total_investment > 0:
    total_pnl = total_value - total_investment
    total_percent = (total_pnl / total_investment) * 100

    color = "🟢" if total_pnl >= 0 else "🔴"

    st.markdown("---")
    st.markdown(f"### {color} Total Value: ₹{total_value:,.0f}")
    st.markdown(f"### {color} Total P&L: ₹{total_pnl:,.0f} ({total_percent:.2f}%)")

# ========================
# 💬 CHAT
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

user = st.chat_input("Ask about stocks...")

if user:
    st.chat_message("user").write(user)
    st.session_state.messages.append({"role": "user", "content": user})

    context = None
    symbol = None

    for word in user.upper().split():
        price, _, _ = get_stock_data(word)
        if price:
            symbol = word
            context = f"{word} price: ₹{price:,.0f}"
            break

    reply = ask_ai(user, context)

    if symbol:
        fig = plot_chart(symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.chat_message("assistant").write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})