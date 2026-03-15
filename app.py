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
# PAGE SETTINGS
# =========================
st.set_page_config(page_title="Market AI Assistant", layout="wide")

# =========================
# CSS
# =========================
st.markdown("""
<style>
.stApp { background-color:#0E1117; }

section[data-testid="stSidebar"]{
    background-color:#0B0E13;
    border-right:1px solid #222;
}

[data-testid="stChatMessage"]{
    background:#161B22;
    border-radius:12px;
    padding:12px;
    margin-bottom:10px;
}

.block-container{
    max-width:900px;
    padding-top:1.5rem;
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
# HELPERS
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

def ask_ai(msg):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are a helpful financial assistant."},
            {"role":"user","content":msg}
        ]
    )
    return response.choices[0].message.content


def get_crypto_price(name):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={name}&vs_currencies=usd"
        data = requests.get(url).json()
        return data[name]["usd"]
    except:
        return None


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


def get_metal_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return data["Close"].iloc[-1]
    except:
        return None


def usd_to_inr(usd):
    try:
        data = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        rate = data["rates"]["INR"]
        return usd * rate
    except:
        return None


def metal_price_table(symbol):

    price_per_ounce = get_metal_price(symbol)

    if not price_per_ounce:
        return None

    # ounce → gram
    price_per_gram_usd = price_per_ounce / 31.1035

    price_10g_usd = price_per_gram_usd * 10
    price_1kg_usd = price_per_gram_usd * 1000

    # fetch exchange rates
    try:
        data = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        rates = data["rates"]
    except:
        return None

    currencies = ["USD","INR","EUR","GBP","AED","JPY"]

    units = {
        "1 Gram": price_per_gram_usd,
        "10 Grams": price_10g_usd,
        "1 Kilogram": price_1kg_usd
    }

    table = {"Unit": []}

    for c in currencies:
        table[c] = []

    for unit, usd_value in units.items():

        table["Unit"].append(unit)

        for c in currencies:

            if c == "USD":
                price = usd_value
            else:
                price = usd_value * rates[c]

            table[c].append(round(price,2))

    import pandas as pd
    return pd.DataFrame(table)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("💹 Market AI")

if st.sidebar.button("➕ New Chat"):
    st.session_state.messages = []

st.sidebar.markdown("---")
st.sidebar.subheader("⭐ Watchlist")

watchlist = ["AAPL","TSLA","NVDA","MSFT","BTC-USD","GC=F","SI=F"]

for s in watchlist:
    try:
        p = yf.Ticker(s).history(period="1d")["Close"].iloc[-1]
        st.sidebar.write(f"{s}  ${p:.2f}")
    except:
        pass

st.sidebar.markdown("---")
st.sidebar.caption("🔴 Live updating every 15s")

# =========================
# MAIN PAGE
# =========================
st.title("💬 Market AI Assistant")
st.caption("Ask about stocks, crypto, gold, silver or markets.")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask anything about markets...")

if user_input:

    st.session_state.messages.append({
        "role":"user",
        "content":user_input
    })

    lower = user_input.lower()
    chart = None
    table = None

    # GOLD
    if "gold" in lower:
        table = metal_price_table("GC=F")
        reply = "🟡 **Gold Price Table**"

    # SILVER
    elif "silver" in lower:
        table = metal_price_table("SI=F")
        reply = "⚪ **Silver Price Table**"

    # CRYPTO
    elif any(c in lower for c in ["bitcoin","ethereum","solana","dogecoin","xrp","cardano"]):
        for c in ["bitcoin","ethereum","solana","dogecoin","xrp","cardano"]:
            if c in lower:
                price = get_crypto_price(c)
                reply = f"{c.title()} is trading at ${price}"
                break

    # STOCKS
    else:
        symbol, company = search_stock(user_input)

        if symbol:
            prediction = predict_next_day(symbol)

if prediction:

    reply = f"""
{company} ({symbol}) is currently trading at ${latest:.2f}

📊 Trend Analysis
Recent trend appears **{prediction['trend']}**

📈 Expected Movement (Next Day)
Estimated range: **${prediction['lower']} – ${prediction['upper']}**
"""
else:
    reply = f"{company} ({symbol}) is trading at ${latest:.2f}"

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