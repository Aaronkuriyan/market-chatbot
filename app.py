import streamlit as st
import yfinance as yf
import os
from groq import Groq
import plotly.graph_objects as go
# ========================
# 🔑 API KEY HANDLING
# ========================
api_key = None

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found. Set it in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ========================
# 🌍 USD → INR (approx)
# ========================
USD_TO_INR = 83


# ========================
# 📊 STOCK PRICE FUNCTION
# ========================
def get_stock_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if data.empty:
            return None

        price = data["Close"].iloc[-1]
        return f"📈 {symbol} Price: ${price:.2f}"

    except:
        return None

# ========================
# 📈 CHART FUNCTION
# ========================
def plot_chart(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1mo")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["Close"],
            mode='lines',
            name='Price'
        ))

        fig.update_layout(
            title=f"{symbol} Price (Last 1 Month)",
            template="plotly_dark"
        )

        return fig

    except:
        return None
    
# ========================
# 🧠 AI INVESTMENT ADVICE
# ========================
def get_investment_advice(context_data):
    try:
        prompt = f"""
You are a financial expert.

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
# 🪙 GOLD PRICE FUNCTION
# ========================
def get_gold_price():
    try:
        data = yf.Ticker("GC=F").history(period="1d")
        if data.empty:
            return None

        usd_price = data["Close"].iloc[-1]
        inr_price = usd_price * USD_TO_INR

        return (
            f"🪙 Gold Price (per ounce):\n"
            f"USD: ${usd_price:.2f}\n"
            f"INR: ₹{inr_price:,.2f}"
        )

    except:
        return None


# ========================
# 🤖 AI FUNCTION
# ========================
def ask_ai(user_input, context_data=None):
    try:
        system_prompt = """
You are a professional financial advisor.

Rules:
- Use real-time data if provided.
- Give structured answers.
- Include insights, risks, and suggestions.
- Be concise but informative.
"""

        user_prompt = user_input

        if context_data:
            user_prompt = f"""
User Question: {user_input}

Real-time Data:
{context_data}

Use this data in your answer.
"""

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
# 🎨 STREAMLIT UI
# ========================
st.set_page_config(page_title="AI Market Chatbot", page_icon="📈")

st.title("📈 AI Market Chatbot")

# ========================
# 💼 PORTFOLIO TRACKER
# ========================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

st.sidebar.title("💼 Portfolio")

symbol = st.sidebar.text_input("Add Stock (e.g. AAPL)")
qty = st.sidebar.number_input("Quantity", min_value=1)

if st.sidebar.button("Add"):
    st.session_state.portfolio[symbol.upper()] = qty

# Show portfolio
for sym, qty in st.session_state.portfolio.items():
    try:
        price = yf.Ticker(sym).history(period="1d")["Close"].iloc[-1]
        value = price * qty
        st.sidebar.write(f"{sym}: {qty} shares = ${value:.2f}")
    except:
        pass

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input
user_input = st.chat_input("Ask about stocks, gold, crypto, or market trends...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    context_data = None

    # ========================
    # 🧠 SMART DETECTION
    # ========================
    lower_query = user_input.lower()

    # GOLD
    if "gold" in lower_query:
        context_data = get_gold_price()

    # STOCKS
    elif any(stock in lower_query for stock in ["aapl", "tsla", "msft", "googl", "amzn", "meta", "nvda"]):
        for word in user_input.upper().split():
            context_data = get_stock_price(word)
            if context_data:
                break

    # ========================
    # 🤖 AI RESPONSE
    # ========================
    with st.spinner("📊 Analyzing market..."):
        ai_reply = ask_ai(user_input, context_data)

    # ========================
# 📊 SHOW CHART
# ========================
if context_data and any(stock in user_input.lower() for stock in ["aapl", "tsla", "msft", "googl", "amzn"]):
    fig = plot_chart(user_input.upper())
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# ========================
# 🧠 AI ADVICE
# ========================
if context_data:
    advice = get_investment_advice(context_data)
    ai_reply += f"\n\n📊 AI Recommendation:\n{advice}"
    # Combine
    if context_data:
        final_reply = f"{context_data}\n\n{ai_reply}"
    else:
        final_reply = ai_reply

    st.chat_message("assistant").write(final_reply)
    st.session_state.messages.append(
        {"role": "assistant", "content": final_reply}
    )