import requests

# Get all crypto names from CoinGecko
def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/list"
    data = requests.get(url).json()
    return data

# Get price of any crypto
def get_crypto_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    data = requests.get(url).json()

    if coin_id in data:
        return data[coin_id]["usd"]
    return None