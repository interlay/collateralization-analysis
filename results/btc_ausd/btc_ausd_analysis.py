# %%
import repackage
repackage.up(2)

from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
import pandas as pd

quote_currency = Token("usd", "USD")
base_currency = Token("acala-dollar", "aUSD")

ausd_pair = Token_Pair(base_currency, quote_currency)
ausd_pair.get_prices()
ausd_pair.calculate_returns()
print(f"aUSD/USD had an annualized std of {ausd_pair.returns.std()[0] *365**0.5}") # the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"aUSD/USD had an annualized mean return of {ausd_pair.calculate_mean_return()}")
# We can disregard the mean return as it is assumed to be 0 for stable coins due to arbitrage

# %%
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# To model this, we get the inverse price to have BTC as quote currency
# If we select the n-th worst trajectories of the inverse price,
# it's equivalent to the n-th best price appreciation.
quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", "BTC")

btc_usd = Token_Pair(base_currency, quote_currency)
btc_usd.get_prices(start_date="2017-07-01", inverse=True)
btc_usd.calculate_returns()

print(f"USD/BTC had an annualized std of {btc_usd.returns.std()[0] *365**0.5}") # the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"USD/BTC had an annualized mean return of {btc_usd.calculate_mean_return()}")

#%%
end_date = btc_usd.returns.index[-2]
while end_date in btc_usd.returns.index:
    start_date = end_date - pd.Timedelta("365D") if end_date - pd.Timedelta("365D") in btc_usd.returns.index else btc_usd.returns.index[0]
    print(f"The volatility of USD/BTC between {start_date} and {end_date} was {btc_usd.returns.loc[start_date:end_date,].values.std()*365**0.5*100}% \n")
    end_date -= pd.Timedelta("365D")


# %%
# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 14 days
# and assume a normal distribution (GBM) with the std of bitcoin over the past 2 years
sim = Simulation(btc_usd, strategy="GBM")
sim.simulate(steps=1,
             maturity=14,
             n_simulations=10_000,
             initial_value=1,
             sigma=btc_usd.returns.std()[0],
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
            "threshold" : None
        },
    "premium_redeem": 
        {
            "periods" : 10,
            "threshold" : None
        },
    "safe_mint": 
        {
            "periods" : 14,
            "threshold" : None
        }
}

for key in thresholds.keys():
    thresholds[key]["threshold"] = simple_analysis.get_threshold_multiplier(alpha=alpha, at_step = thresholds[key]["periods"])

print(thresholds)

#%%
# analysing the historic VaR for KSM/BTC as a sanity check
durations_in_days = [7,10,14]

for duration in durations_in_days:
    hist_var = btc_usd.prices.pct_change(duration).dropna()
    hist_var = hist_var.sort_values("Price", ascending=False)
    var_alpha = hist_var.iloc[int(len(hist_var) * alpha),]
    
    print(f"The historic VaR for a confidence level of {alpha*100}% of USD/BTC for {duration}] days was: {round(var_alpha[0] *100,3)}% \n")
    print(f"The thresholds based on historic VaR adjusted for liquidity are : {1/ (1 + var_alpha[0])}")
# %%
