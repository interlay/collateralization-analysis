# %%
import repackage
repackage.up(2)

from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
import pandas as pd
from datetime import datetime

# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# To model this, we get the inverse price to have BTC as quote currency
# If we select the n-th worst trajectories of the inverse price,
# it's equivalent to the n-th best price appreciation.
btc = Token("bitcoin", "btc")
usdt = Token("tether", "usdt")

btc_usdt = Token_Pair(usdt, btc)
btc_usdt.get_prices(start_date="2017-07-01")
btc_usdt.calculate_returns()

print(f"USDT/BTC had an annualized std of {btc_usdt.returns.std()[0] *365**0.5}") # the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"USDT/BTC had an annualized mean return of {btc_usdt.calculate_mean_return()}")

#%%
end_date = btc_usdt.returns.index[-2]
while end_date in btc_usdt.returns.index:
    start_date = end_date - pd.Timedelta("365D") if end_date - pd.Timedelta("365D") in btc_usdt.returns.index else btc_usdt.returns.index[0]
    print(f"The volatility of USDT/BTC between {start_date} and {end_date} was {btc_usdt.returns.loc[start_date:end_date,].values.std()*365**0.5*100}% \n")
    end_date -= pd.Timedelta("365D")


# %%
# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 20,000 trajectories with a duration of 21 days
# and assume a normal distribution (GBM) with the std of bitcoin over the past 2 years
start_date = (datetime.today() - pd.Timedelta("730D")).strftime("%Y-%m-%d")
btc_usdt.get_prices(start_date=start_date, inverse=True)
btc_usdt.calculate_returns()

sim = Simulation(btc_usdt, strategy="GBM")
sim.simulate(steps=1,
             maturity=21,
             n_simulations=20_000,
             initial_value=1,
             sigma=btc_usdt.returns.std()[0],
             mu=0)

#%%
# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)
alpha = 0.99

thresholds = {
    "liquidation": 
        {
            "periods" : 7,
            "analytical_threshold" : None,
            "historical_threshold" : None
        },
    "premium_redeem": 
        {
            "periods" : 10,
            "analytical_threshold" : None,
            "historical_threshold" : None
        },
    "safe_mint": 
        {
            "periods" : 21,
            "analytical_threshold" : None,
            "historical_threshold" : None
        }
}

for key, threshold in thresholds.items():
    threshold["analytical_threshold"] = simple_analysis.get_threshold_multiplier(alpha=alpha, at_step = thresholds[key]["periods"])
    hist_var = btc_usdt.prices.pct_change(threshold["periods"]).dropna()
    hist_var = hist_var.sort_values("Price", ascending=False)
    threshold["historical_threshold"] = 1/(1+hist_var.iloc[int(len(hist_var) * alpha),][0])
    
    print(f"The {key} threshold based on the analytical VaR for a confidence level of {alpha*100}% of USDT/BTC over {threshold['periods']} is: {round(threshold['analytical_threshold'] *100,3)}%")
    print(f"The {key} threshold based on the historic VaR for a confidence level of {alpha*100}% of USDT/BTC over {threshold['periods']} is: {round(threshold['historical_threshold'] *100,3)}% \n")
# %%
