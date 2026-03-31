import streamlit as st
import yfinance as yf
import os
from groq import Groq
import plotly.graph_objects as go

# ========================
# 🔑 API KEY
# ========================
api_key = None

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found.")
    st.stop()

client = Groq(api_key=api_key)

# ========================
# 🌍 USD → INR (LIVE)
# ========================
def get_usd_to_inr():
    try:
        data = yf.Ticker("INR=X").history(period="1d")
        return data["Close"].iloc[-1]
    except:
        return 83


# ========================
# 📊 STOCK PRICE (INR)
# ========================
def get_stock_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if data.empty:
            return None

        usd_price = data["Close"].iloc[-1]
        rate = get_usd_to_inr()
        inr_price = usd_price * rate

        return f"📈 {symbol} Price: ₹{inr_price:,.2f}"
    except:
        return None


# ========================
# 🪙 GOLD PRICE (INR)
# ========================
def get_gold_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")
        if data.empty:
            return None

        usd_price = data["Close"].iloc[-1]
        rate = get_usd_to_inr()
        inr_price = usd_price * rate

        return f"🪙 Gold Price: ₹{inr_price:,.2f} (per ounce)"
    except:
        return None


# ========================
# 📈 CHART (INR)
# ========================
def plot_chart(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1mo")
        rate = get_usd_to_inr()

        data["INR"] = data["Close"] * rate

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["INR"],
            mode='lines',
            name='Price (₹)'
        ))

        fig.update_layout(
            title=f"{symbol} Price (INR - 1 Month)",
            template="plotly_dark",
            yaxis_title="Price (₹)"
        )

        return fig
    except:
        return None


# ========================
# 🧠 AI ADVICE
# ========================
def get_investment_advice(context_data):
    try:
        prompt = f"""
You are a financial expert.

All prices are in INR.

Based on this data:
{context_data}

Give:
- Buy / Hold / Sell
- Reason
- Risk level
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
    except Exception as e:
        return str(e)


# ========================
# 🤖 AI RESPONSE
# ========================
def ask_ai(user_input, context_data=None):
    try:
        system_prompt = """
You are a professional financial advisor.

All prices are in INR (₹).

Give:
- Clear insights
- Risks
- Suggestions
"""

        if context_data:
            user_prompt = f"""
User Question: {user_input}

Real-time Data:
{context_data}
"""
        else:
            user_prompt = user_input

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {str(e)}"


# ========================
# 🎨 UI
# ========================
st.set_page_config(page_title="AI Market Chatbot", page_icon="📈")
st.title("📈 AI Market Chatbot (INR)")

# ========================
# 💼 PORTFOLIO
# ========================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

st.sidebar.title("💼 Portfolio")

symbol = st.sidebar.text_input("Add Stock (e.g. AAPL)")
qty = st.sidebar.number_input("Quantity", min_value=1)

if st.sidebar.button("Add") and symbol:
    st.session_state.portfolio[symbol.upper()] = qty

for sym, qty in st.session_state.portfolio.items():
    try:
        data = yf.Ticker(sym).history(period="1d")
        price = data["Close"].iloc[-1]
        rate = get_usd_to_inr()

        inr_price = price * rate
        value = inr_price * qty

        st.sidebar.write(f"{sym}: {qty} shares = ₹{value:,.2f}")
    except:
        pass


# ========================
# 💬 CHAT HISTORY
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# ========================
# 💬 USER INPUT
# ========================
user_input = st.chat_input("Ask about stocks, gold, or market trends...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    context_data = None
    detected_symbol = None
    lower_query = user_input.lower()

    # GOLD
    if "gold" in lower_query:
        context_data = get_gold_price()

    # STOCKS
    elif any(stock in lower_query for stock in ["aapl", "tsla", "msft", "googl", "amzn", "meta", "nvda"]):
        for word in user_input.upper().split():
            detected_symbol = word
            context_data = get_stock_price(word)
            if context_data:
                break

    # AI RESPONSE
    with st.spinner("📊 Analyzing market..."):
        ai_reply = ask_ai(user_input, context_data)

    # CHART
    if detected_symbol:
        fig = plot_chart(detected_symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # AI ADVICE
    if context_data:
        advice = get_investment_advice(context_data)
        ai_reply += f"\n\n📊 **AI Investment Insight:**\n{advice}"

    # FINAL RESPONSE
    if context_data:
        final_reply = f"{context_data}\n\n{ai_reply}"
    else:
        final_reply = ai_reply

    st.chat_message("assistant").write(final_reply)
    st.session_state.messages.append(
        {"role": "assistant", "content": final_reply}
    )