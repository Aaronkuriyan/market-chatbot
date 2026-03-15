import streamlit as st
import plotly.express as px
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from groq import Groq
from dotenv import load_dotenv
import os
import pandas as pd

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(page_title="Market AI Assistant", layout="wide")

# =========================
# STYLE
# =========================

st.markdown("""
<style>
.stApp { background-color:#0E1117; }

section[data-testid="stSidebar"]{
    background-color:#0B0E13;
}

[data-testid="stChatMessage"]{
    background:#161B22;
    border-radius:12px;
    padding:12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# ENV + AI
# =========================

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# =========================
# AUTO REFRESH
# =========================

st_autorefresh(interval=15000, key="refresh")

# =========================
# AI RESPONSE
# =========================

def ask_ai(msg):

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are a helpful financial assistant."},
            {"role":"user","content":msg}
        ]
    )

    return response.choices[0].message.content


# =========================
# STOCK SEARCH
# =========================

def search_stock(query):

    try:
        results = yf.Search(query).quotes

        if results:
            return results[0]["symbol"], results[0]["shortname"]

    except:
        pass

    return None, None


def get_stock_history(symbol):

    return yf.Ticker(symbol).history(period="1mo")


# =========================
# NEXT DAY PREDICTION
# =========================

def predict_next_day(symbol):

    data = yf.Ticker(symbol).history(period="5d")

    if len(data) < 2:
        return None

    last_price = data["Close"].iloc[-1]
    prev_price = data["Close"].iloc[-2]

    change = last_price - prev_price

    predicted = last_price + change

    lower = predicted * 0.98
    upper = predicted * 1.02

    trend = "bullish 📈" if change > 0 else "bearish 📉"

    return {
        "trend": trend,
        "lower": round(lower,2),
        "upper": round(upper,2)
    }


# =========================
# CRYPTO
# =========================

def get_crypto_price(name):

    try:

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={name}&vs_currencies=usd"
        data = requests.get(url).json()

        return data[name]["usd"]

    except:

        return None


# =========================
# METAL PRICE
# =========================

def get_metal_price(symbol):

    try:

        data = yf.Ticker(symbol).history(period="1d")

        return data["Close"].iloc[-1]

    except:

        return None


# =========================
# METAL TABLE MULTI-CURRENCY
# =========================

def metal_price_table(symbol):

    ounce_price = get_metal_price(symbol)

    if not ounce_price:
        return None

    gram_usd = ounce_price / 31.1035

    units = {
        "1 Gram": gram_usd,
        "10 Grams": gram_usd * 10,
        "1 Kilogram": gram_usd * 1000
    }

    rates = requests.get(
        "https://api.exchangerate-api.com/v4/latest/USD"
    ).json()["rates"]

    currencies = ["USD","INR","EUR","GBP","AED","JPY"]

    table = {"Unit": list(units.keys())}

    for currency in currencies:

        values = []

        for usd in units.values():

            if currency == "USD":
                values.append(round(usd,2))
            else:
                values.append(round(usd * rates[currency],2))

        table[currency] = values

    return pd.DataFrame(table)


# =========================
# SIDEBAR
# =========================

st.sidebar.title("Market AI")

if st.sidebar.button("New Chat"):

    st.session_state.messages = []

st.sidebar.markdown("---")
st.sidebar.subheader("Watchlist")

watchlist = ["AAPL","TSLA","NVDA","MSFT","BTC-USD","GC=F","SI=F"]

for s in watchlist:

    try:

        price = yf.Ticker(s).history(period="1d")["Close"].iloc[-1]

        st.sidebar.write(f"{s}  ${price:.2f}")

    except:

        pass

st.sidebar.caption("Live update every 15 seconds")

# =========================
# MAIN PAGE
# =========================

st.title("Market AI Assistant")

st.caption("Ask about stocks, crypto, gold, silver or markets.")

if "messages" not in st.session_state:

    st.session_state.messages = []

user_input = st.chat_input("Ask anything about markets...")

if user_input:

    st.session_state.messages.append({
        "role":"user",
        "content":user_input
    })

    chart = None
    table = None
    reply = None

    lower = user_input.lower()

# =========================
# GOLD
# =========================

    if "gold" in lower:

        table = metal_price_table("GC=F")

        reply = "Gold price table"

# =========================
# SILVER
# =========================

    elif "silver" in lower:

        table = metal_price_table("SI=F")

        reply = "Silver price table"

# =========================
# CRYPTO
# =========================

    elif "bitcoin" in lower:

        price = get_crypto_price("bitcoin")

        reply = f"Bitcoin is trading at ${price}"

# =========================
# STOCKS
# =========================

    else:

        symbol, company = search_stock(user_input)

        if symbol:

            data = get_stock_history(symbol)

            if not data.empty:

                chart = px.line(
                    data,
                    x=data.index,
                    y="Close",
                    title=f"{company} ({symbol}) - 1 Month"
                )

                latest = data["Close"].iloc[-1]

                prediction = predict_next_day(symbol)

                if prediction:

                    reply = f"""
{company} ({symbol}) is currently trading at ${latest:.2f}

Trend: {prediction['trend']}

Expected next-day range:
${prediction['lower']} – ${prediction['upper']}
"""

                else:

                    reply = f"{company} ({symbol}) is trading at ${latest:.2f}"

        else:

            reply = ask_ai(user_input)

    st.session_state.messages.append({
        "role":"assistant",
        "content":reply,
        "chart":chart,
        "table":table
    })

# =========================
# DISPLAY CHAT
# =========================

for m in st.session_state.messages:

    with st.chat_message(m["role"]):

        st.write(m["content"])

        if m.get("table") is not None:
            st.table(m["table"])

        if m.get("chart"):
            st.plotly_chart(m["chart"], use_container_width=True)