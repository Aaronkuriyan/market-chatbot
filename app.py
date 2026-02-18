import streamlit as st
import plotly.express as px
import yfinance as yf
import requests
from streamlit_autorefresh import st_autorefresh
from groq import Groq
from dotenv import load_dotenv
import os

# =========================
# PAGE SETTINGS
# =========================
st.set_page_config(page_title="Market AI Assistant", layout="wide")

# ---------- PRO CSS ----------
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
# COMMODITIES
# =========================
COMMODITIES = {
    "gold": "GC=F",
    "silver": "SI=F",
    "oil": "CL=F",
    "crude oil": "CL=F",
    "natural gas": "NG=F",
    "copper": "HG=F",
    "platinum": "PL=F",
    "palladium": "PA=F"
}

# =========================
# HELPERS
# =========================

def ask_ai(msg):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are a helpful financial market assistant."},
            {"role":"user","content":msg}
        ]
    )
    return response.choices[0].message.content


def get_metal_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return data["Close"].iloc[-1]
    except:
        return None


def get_crypto_price(name):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={name}&vs_currencies=usd"
        data = requests.get(url, timeout=10).json()
        return data[name]["usd"] if name in data else None
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
st.caption("Ask about stocks, crypto, gold, silver, or commodities.")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask anything about markets...")

if user_input:

    st.session_state.messages.append({
        "role":"user",
        "content":user_input
    })

    chart = None
    lower = user_input.lower()
    reply = None

    # ----- AUTO COMMODITY DETECTION -----
    commodity_found = None

    for name, symbol in COMMODITIES.items():
        if name in lower:
            commodity_found = name
            price = get_metal_price(symbol)
            if price:
                reply = f"{commodity_found.title()} is currently trading at ${price:.2f}"
            break

    # ----- AUTO CRYPTO -----
    if reply is None:
        for c in ["bitcoin","ethereum","solana","dogecoin","xrp","cardano"]:
            if c in lower:
                price = get_crypto_price(c)
                if price:
                    reply = f"{c.title()} is trading at ${price}"
                break

    # ----- AUTO STOCK -----
    if reply is None:
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
                reply = f"{company} ({symbol}) is trading at ${latest:.2f}"

    # ----- NORMAL AI -----
    if reply is None:
        with st.spinner("AI is thinking..."):
            reply = ask_ai(user_input)

    st.session_state.messages.append({
        "role":"assistant",
        "content":reply,
        "chart":chart
    })

# =========================
# DISPLAY CHAT
# =========================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("chart"):
            st.plotly_chart(m["chart"], use_container_width=True)
