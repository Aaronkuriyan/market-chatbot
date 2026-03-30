import streamlit as st
from openai import OpenAI
import yfinance as yf
import streamlit as st
import os

api_key = None

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found.")
    st.stop()

from groq import Groq

client = Groq(api_key=api_key)

# ========================
# 📊 STOCK DATA FUNCTION
# ========================
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")

        if data.empty:
            return None

        price = data["Close"].iloc[-1]
        return f"📊 Current price of {symbol} is ${price:.2f}"

    except:
        return None


# ========================
# 🤖 AI FUNCTION
# ========================
def ask_ai(user_input):
    try:
        prompt = f"""
You are a professional financial advisor and market expert.

Give a detailed answer including:
- Explanation
- Market insights
- Risks
- Actionable advice

User Question: {user_input}
"""

        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {str(e)}"

    except Exception as e:
        return f"❌ AI Error: {str(e)}"


# ========================
# 🎨 STREAMLIT UI
# ========================
st.set_page_config(page_title="Market Chatbot", page_icon="📈")

st.title("📈 AI Market Chatbot")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show old messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input box
user_input = st.chat_input("Ask about stocks, crypto, or market trends...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ========================
    # 🧠 STOCK DETECTION
    # ========================
    stock_response = None

    valid_symbols = [
        "AAPL", "TSLA", "GOOGL", "MSFT",
        "AMZN", "META", "NFLX", "NVDA"
    ]

    words = user_input.upper().split()

    for word in words:
        if word in valid_symbols:
            stock_response = get_stock_data(word)
            break

    # "price of XYZ"
    if not stock_response and "price of" in user_input.lower():
        try:
            symbol = user_input.split()[-1].upper()
            stock_response = get_stock_data(symbol)
        except:
            pass

    # ========================
    # 🤖 AI RESPONSE
    # ========================
    with st.spinner("📊 Analyzing market..."):
        ai_reply = ask_ai(user_input)

    final_reply = (
        f"{stock_response}\n\n{ai_reply}" if stock_response else ai_reply
    )

    st.chat_message("assistant").write(final_reply)
    st.session_state.messages.append(
        {"role": "assistant", "content": final_reply}
    )