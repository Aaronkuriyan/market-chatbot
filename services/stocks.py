import yfinance as yf


def search_stock_symbol(query):
    results = yf.Search(query).quotes

    if results and len(results) > 0:
        return results[0]["symbol"], results[0]["shortname"]

    return None, None


def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")

    if not data.empty:
        return data["Close"].iloc[-1]

    return None


# ⭐ NEW: Get history for charts
def get_stock_history(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")
    return data