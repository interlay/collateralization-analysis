from extract.connections import extract_coingecko
from load.coingecko_rates import CoingeckoRates

# Coingecko tracks prices using their own IDs
# https://api.coingecko.com/api/v3/coins/list
# Example
# {
#  "id": "bitcoin",
#  "symbol": "btc",
#  "name": "Bitcoin"
# }
TOKEN_SYMBOL_TO_COINGECKO_ID = {
    # Native tokens on Interlay/Kintsugi
    "IBTC": "bitcoin",  # USe BTC price
    "KBTC": "bitcoin",  # Use BTC price
    "KSM": "kusama",
    "DOT": "polkadot",
    "INTR": "interlay",
    "KINT": "kintsugi",
    # Foreign assets
    "USDT": "tether",
    "GLMR": "moonbeam",
    "MOVR": "moonriver",
    "LKSM": "liquid-ksm",
    "AUSD": "acala-dollar",  # Karura version
    "AUSD": "acala-dollar-acala",  # Acala version
    "KAR": "karura",
    # "SKSM": "tron",  # Unsupported
    # "VKSM": "ripple",  # Unsupported
    "ETH": "ethereum",
}


async def get_latest_coingecko_rates(token_symbols):
    """
    Attempts to load the coingecko rates from a local database.
    If this fails, it will attempt to load the rates from the coingecko API.
    """
    rates = await get_coingecko_rates_from_api(token_symbols)
    return rates


async def get_coingecko_rates_from_api(token_symbols=None):
    # Alternatively, get them from the API
    if not token_symbols:
        token_symbols = TOKEN_SYMBOL_TO_COINGECKO_ID.keys()

    coingecko_ids = []
    for symbol in token_symbols:
        try:
            coingecko_ids.append(TOKEN_SYMBOL_TO_COINGECKO_ID[symbol])
        except KeyError:
            print("Token {} not found in coingecko map".format(symbol))
            continue

    query = "simple/price"
    args = "ids={}&vs_currencies=usd&precision=5".format(",".join(coingecko_ids))
    coingecko_rates = await extract_coingecko(query, args)

    # Map the coingecko ids back to the token symbols accounting for the
    # iBTC/kBTC special case
    rates = {}
    for symbol in token_symbols:
        if symbol in TOKEN_SYMBOL_TO_COINGECKO_ID:
            coingecko_id = TOKEN_SYMBOL_TO_COINGECKO_ID[symbol]
            usd_rate = coingecko_rates[coingecko_id]["usd"]
        else:
            # Default to 0 if the token is not found
            usd_rate = 0.0
            coingecko_id = None
            print("Token {} not found in coingecko rates".format(symbol))

        rates[symbol] = {
            "usdRate": usd_rate,
            "coingeckoId": coingecko_id,
        }

    return rates
