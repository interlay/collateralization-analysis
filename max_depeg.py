# %%
import yaml
from data.data_request import Token, Token_Pair
from datetime import datetime, timedelta

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

start_date = (datetime.today() - timedelta(365 * 6)).strftime("%Y-%m-%d")

NETWORK = "kusama"
# %%

for ticker, token in config["collateral"][NETWORK].items():
    if token.get("proxy"):
        proxy_ticker, proxy_name = next(iter(token.get("proxy").items()))
        token_usd = Token_Pair(Token(token["name"], ticker), Token("dollar", "usd"))
        proxy_usd = Token_Pair(Token(proxy_name, proxy_ticker), Token("dollar", "usd"))
        try:
            token_usd.get_prices(start_date=start_date)

            if proxy_ticker == "usd":
                proxy_usd.prices = 1
            else:
                proxy_usd.get_prices(start_date=start_date)

            token_proxy_prices = token_usd.prices / proxy_usd.prices
            token_proxy_returns = token_proxy_prices.pct_change().dropna()
            max_depeg = round(token_proxy_returns.add(1).cumprod().sub(1).min()[0], 3)
            print(f"Max depeg for {token_usd.base_token.ticker} was {max_depeg * 100}%")
        except (KeyError, AttributeError) as e:
            print(f"No prices available for {token_usd.base_token.ticker}")
            continue
# %%
