# %%
# %%
import repackage
repackage.up(2)

from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation

quote_currency = Token("usd", "USD")
base_currency = Token("acala-dollar", "aUSD")

ausd_pair = Token_Pair(base_currency, quote_currency)
ausd_pair.get_prices()
ausd_pair.calculate_returns()
print(f"aUSD/USD had an annualized std of {ausd_pair.returns.std()[0] *365**0.5}") # the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"aUSD/USD had an annualized mean return of {ausd_pair.calculate_mean_return()}")
# We can disregard the mean return as it is assumed to be 0 for stable coins due to arbitrage
# We have to take into consideration the standard deviation of the price, which we will
# add to the standard deviation of BTC

# %%
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# To model this, we get the inverse price to have BTC as quote currency
# If we select the n-th worst trajectories of the inverse price,
# it's equivalent to the n-th best price appreciation.
# We choose a 5 year period to get a decent sample period with 3 bull runs & crashes
quote_currency = Token("usd", "USD")
base_currency = Token("bitcoin", "BTC")

btc_pair = Token_Pair(base_currency, quote_currency)
btc_pair.get_prices(start_date="2017-07-01", inverse=True)
btc_pair.calculate_returns()

print(f"USD/BTC had an annualized std of {btc_pair.returns.std()[0] *365**0.5}") # the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"USD/BTC had an annualized mean return of {btc_pair.calculate_mean_return()}")

# %%
# We adjust the variance by adding the covariance of the aUSD/USD pair.
corr = ausd_pair.returns.corrwith(btc_pair.returns)
cov = corr * btc_pair.returns.std()[0] * ausd_pair.returns.std()[0]
# daily var, add 2*covariance and take the square root to get the std
adj_btc_std = (btc_pair.returns.var()[0] + 2 * cov) ** 0.5

# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 10 days and 24 hours each
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(btc_pair, strategy="GBM")
sim.simulate(steps=24,
             maturity=7,
             n_simulations=10_000,
             initial_value=1,
             sigma=adj_btc_std[0],
             mu=0)


# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below 1 only with a 0.1% chance in 10 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
liquidation_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.999) # <- this can be changed ofc 
premium_redeem_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.90) # <- this can be changed ofc 

print(f"The estimated liquidation threshold is ~{int(liquidation_threshold_margin * 100)}% of the debt value")
print(f"The estimated premium redeem threshold is ~{int(liquidation_threshold_margin * premium_redeem_threshold_margin * 100)}% of the debt value")

# %%

# We adjust the variance by adding the covariance of the aUSD/USD pair.
corr = ausd_pair.returns.corrwith(btc_pair.returns)
cov = corr * btc_pair.returns.std()[0] * ausd_pair.returns.std()[0]
# daily var, add 2*covariance and take the square root to get the std
adj_btc_std = (btc_pair.returns.var()[0] + 2 * cov) ** 0.5

# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 10 days and 24 hours each
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(btc_pair, strategy="GBM")
sim.simulate(steps=24,
             maturity=21,
             n_simulations=10_000,
             initial_value=1,
             sigma=adj_btc_std[0],
             mu=0)



# %%

# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below the liquidation_threshold_margin with a 10% chance in 21 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
secure_threshold_margin = simple_analysis.get_threshold_multiplier(alpha=0.90) # <- this can be changed ofc 

print(f"The estimated secure threshold is ~{int(liquidation_threshold_margin * secure_threshold_margin * 100)}% of the debt value")

# %%



