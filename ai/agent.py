from groq import Groq
from dotenv import load_dotenv
import os

from services.crypto import get_all_coins, get_crypto_price
from services.stocks import search_stock_symbol, get_stock_price

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

COINS = get_all_coins()


# ---------- CRYPTO DETECTION ----------
def detect_coin(user_text):
    text = user_text.lower()

    for coin in COINS:
        name = coin["name"].lower()
        symbol = coin["symbol"].lower()

        if name in text or symbol in text:
            return coin["id"], coin["name"]

    return None, None


# ---------- MAIN AI ----------
def ask_ai(user_message):

    # 🔥 Auto crypto detection
    coin_id, coin_name = detect_coin(user_message)

    if coin_id:
        price = get_crypto_price(coin_id)
        if price:
            return f"{coin_name} is currently trading at ${price}"

    # 🔥 Auto stock detection
    symbol, company = search_stock_symbol(user_message)

    if symbol:
        price = get_stock_price(symbol)

        if price:
            return f"{company} ({symbol}) is trading at ${price:.2f}"

    # Normal AI response
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content