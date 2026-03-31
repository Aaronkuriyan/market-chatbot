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
# 🪙 GOLD PRICE (REALISTIC INDIA)
# ========================
def get_gold_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")

        usd_per_ounce = data["Close"].iloc[-1]
        rate = get_rate()

        # Convert to INR per gram
        inr_per_gram = (usd_per_ounce * rate) / 28.35

        # 🔥 ADJUSTMENT FACTOR (IMPORTANT)
        # Adds import duty + GST + retail markup
        adjusted_price = inr_per_gram * 1.12

        return (
            f"🪙 Gold Price (India Estimate):\n"
            f"₹{adjusted_price:,.0f} per gram\n"
            f"(includes taxes & retail margin)"
        )

    except:
        return "Error fetching gold price"

# ========================
# 📈 CHART
# ========================
def plot_chart(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1mo")
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
            title=f"{symbol} Chart (INR)",
            xaxis_rangeslider_visible=False
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
st.set_page_config(page_title="AI Market Chatbot", page_icon="📈")
st.title("📈 AI Market Chatbot")

# ========================
# 💼 PORTFOLIO
# ========================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

st.sidebar.title("💼 Portfolio")

sym = st.sidebar.text_input("Add Stock (AAPL)")
qty = st.sidebar.number_input("Quantity", min_value=1)

if st.sidebar.button("Add") and sym:
    price, _, _ = get_stock(sym.upper())
    if price:
        st.session_state.portfolio[sym.upper()] = {
            "qty": qty,
            "buy": price
        }

# Portfolio Display
for s, d in st.session_state.portfolio.items():
    curr, _, _ = get_stock(s)

    if curr:
        value = curr * d["qty"]
        pnl = value - (d["buy"] * d["qty"])
        percent = (pnl / (d["buy"] * d["qty"])) * 100

        color = "🟢" if pnl >= 0 else "🔴"

        st.sidebar.write(
            f"{color} {s} → ₹{value:,.0f} ({percent:.2f}%)"
        )

# ========================
# 💬 CHAT
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user = st.chat_input("Ask about stocks, gold, or market trends...")

if user:
    st.chat_message("user").write(user)
    st.session_state.messages.append({"role": "user", "content": user})

    context = None
    symbol = None

    if "gold" in user.lower():
        context = get_gold_price()
    else:
        for word in user.upper().split():
            price, _, _ = get_stock(word)
            if price:
                symbol = word
                context = f"{word} price ₹{price:,.0f}"
                break

    reply = ask_ai(user, context)

    # Chart
    if symbol:
        fig = plot_chart(symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.chat_message("assistant").write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})