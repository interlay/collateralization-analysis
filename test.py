#%%
import yaml
from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
from datetime import datetime, timedelta
from helper import round_up_to_nearest_5, get_total_risk_adjustment, print_banner
import logging
import sys
import pandas as pd
import numpy as np

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

ALPHA = config["analysis"]["alpha"]
PERIODS = config["analysis"]["thresholds"]["periods"]

start_date = (
    datetime.today() - timedelta(config["analysis"]["historical_sample_period"])
).strftime("%Y-%m-%d")

tokens = [
    Token("bitcoin", "BTC"),
    Token("ethereum", "ETH"),
    Token("kusama", "KSM"),
    Token("kintsugi", "KINT"),
    Token("liquid-ksm", "LKSM"),
    Token("moonriver", "MOVR"),
]
# %%
assets = []
for token in tokens:
    token_pair = Token_Pair(token, Token("dollar", "USD"))
    token_pair.get_prices(start_date=start_date)
    token_pair.calculate_returns()
    assets.append(token_pair)
# %%
returns = pd.DataFrame()
for asset in assets:
    if len(asset.prices) > 1:
        returns = returns.join(asset.returns, how="outer")
        returns.rename(columns={"Price": asset.pair_ticker()}, inplace=True)
#%%
weights = np.array([1, 0, 0, 0, ,0 0])
std = (weights.dot(returns.cov().values).dot(weights.transpose()) * 365) ** 0.5

print(f"Annualized volatility of the portfolio would be {std * 100}%")
# %%
