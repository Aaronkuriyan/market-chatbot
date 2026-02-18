import requests

def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/list"

    try:
        data = requests.get(url, timeout=10).json()
        return data
    except:
        return []   # Prevent crash if internet fails


def get_crypto_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"

    try:
        data = requests.get(url, timeout=10).json()

        if coin_id in data:
            return data[coin_id]["usd"]
    except:
        return None

    return None